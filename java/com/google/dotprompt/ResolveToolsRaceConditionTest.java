/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.google.dotprompt;

import static com.google.common.truth.Truth.assertThat;

import com.google.dotprompt.models.ParsedPrompt;
import com.google.dotprompt.models.PromptMetadata;
import com.google.dotprompt.models.ToolDefinition;
import com.google.dotprompt.resolvers.ToolResolver;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * Concurrency test for resolveTools method targeting specific race conditions: 1. Line 450:
 * toolDefs.add() without synchronization (when tool is registered) 2. Lines 557-558, 565-566: config
 * map modification without synchronization 3. Data consistency issues between toolDefs and
 * unresolvedTools
 */
@RunWith(JUnit4.class)
public class ResolveToolsRaceConditionTest {

  /**
   * Test race condition at line 450: toolDefs.add() without synchronization. When multiple threads
   * simultaneously call resolveTools with tools that exist in toolDefinitions, they each modify
   * their own toolDefs list (no problem). But we need to verify that ArrayList.add is safe when
   * only one thread is adding to each instance.
   */
  @Test
  public void testLine450_raceCondition() throws Exception {
    int numThreads = 50;
    int iterationsPerThread = 50;

    Map<String, ToolDefinition> tools = Map.of(
        "tool1", new ToolDefinition("tool1", "Tool 1", Map.of(), null),
        "tool2", new ToolDefinition("tool2", "Tool 2", Map.of(), null),
        "tool3", new ToolDefinition("tool3", "Tool 3", Map.of(), null));

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CyclicBarrier barrier = new CyclicBarrier(numThreads);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<Throwable> exceptions = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      executor.submit(
          () -> {
            try {
              // All threads start at the same time
              barrier.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  List<String> toolsList = List.of("tool1", "tool2", "tool3");
                  Map<String, Object> config = Map.of("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(5, TimeUnit.SECONDS);

                  // Verify all tools were resolved
                  assertThat(metadata.toolDefs()).hasSize(3);
                  assertThat(metadata.tools()).isNull(); // All tools resolved

                } catch (Exception e) {
                  synchronized (exceptions) {
                    exceptions.add(e);
                  }
                  errors.incrementAndGet();
                }
              }
            } catch (Exception e) {
              synchronized (exceptions) {
                exceptions.add(e);
              }
              errors.incrementAndGet();
            } finally {
              endLatch.countDown();
            }
          });
    }

    endLatch.await(30, TimeUnit.SECONDS);
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Line 450 Race Condition Test ===");
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Errors: " + errors.get());

    if (!exceptions.isEmpty()) {
      System.out.println("\nExceptions:");
      for (Throwable t : exceptions.subList(0, Math.min(10, exceptions.size()))) {
        System.out.println(t.getClass().getName() + ": " + t.getMessage());
      }
    }

    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Test the actual potential race: when one thread modifies config while another reads it. This
   * tests if the config map can be corrupted.
   */
  @Test
  public void testConfigMapRaceCondition() throws Exception {
    int numThreads = 30;
    int iterationsPerThread = 100;

    Map<String, ToolDefinition> tools =
        Map.of("tool1", new ToolDefinition("tool1", "Tool 1", Map.of(), null));

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CyclicBarrier barrier = new CyclicBarrier(numThreads);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<String> errorMessages = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      final int threadId = i;
      executor.submit(
          () -> {
            try {
              barrier.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // Create new config each time - but same structure
                  List<String> toolsList = new ArrayList<>();
                  toolsList.add("tool1");
                  if ((threadId + j) % 2 == 0) {
                    toolsList.add("nonexistent_tool"); // Goes to line 552
                  }

                  Map<String, Object> config = new java.util.HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(5, TimeUnit.SECONDS);

                  // Verify config wasn't corrupted
                  assertThat(metadata).isNotNull();

                } catch (Exception e) {
                  errorMessages.add(e.getClass().getName() + ": " + e.getMessage());
                  errors.incrementAndGet();
                }
              }
            } catch (Exception e) {
              errorMessages.add("Setup: " + e.getClass().getName() + ": " + e.getMessage());
              errors.incrementAndGet();
            } finally {
              endLatch.countDown();
            }
          });
    }

    endLatch.await(30, TimeUnit.SECONDS);
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Config Map Race Condition Test ===");
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Errors: " + errors.get());

    if (!errorMessages.isEmpty()) {
      System.out.println("\nFirst 10 errors:");
      errorMessages.stream().limit(10).forEach(System.out::println);
    }

    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Test with ToolResolver to trigger the synchronized blocks in callbacks. This tests if the
   * synchronization at lines 463, 477, 481, 486, etc. is correct.
   */
  @Test
  public void testAsyncResolverRaceCondition() throws Exception {
    int numThreads = 30;
    int iterationsPerThread = 50;

    // Create a resolver that completes async
    AtomicInteger resolutionCount = new AtomicInteger(0);
    ToolResolver resolver =
        toolName -> {
          return CompletableFuture.supplyAsync(
              () -> {
                resolutionCount.incrementAndGet();
                // Simulate some work
                try {
                  Thread.sleep(1);
                } catch (InterruptedException e) {
                  Thread.currentThread().interrupt();
                }
                if (toolName.startsWith("dyn_")) {
                  return new ToolDefinition(toolName, "Dynamic tool", Map.of(), null);
                }
                return null;
              });
        };

    Map<String, ToolDefinition> staticTools =
        Map.of("static1", new ToolDefinition("static1", "Static 1", Map.of(), null));

    Dotprompt dp =
        new Dotprompt(
            DotpromptOptions.builder().setTools(staticTools).setToolResolver(resolver).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CyclicBarrier barrier = new CyclicBarrier(numThreads);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<Throwable> exceptions = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      executor.submit(
          () -> {
            try {
              barrier.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  List<String> toolsList = List.of("static1", "dyn_tool_a", "dyn_tool_b", "unknown");

                  Map<String, Object> config = new java.util.HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(10, TimeUnit.SECONDS);

                  // Verify results
                  assertThat(metadata).isNotNull();
                  // Should have 3 toolDefs: static1 + 2 dynamic
                  assertThat(metadata.toolDefs()).hasSize(3);
                  // Should have 1 unresolved: unknown
                  assertThat(metadata.tools()).contains("unknown");

                } catch (Exception e) {
                  synchronized (exceptions) {
                    exceptions.add(e);
                  }
                  errors.incrementAndGet();
                }
              }
            } catch (Exception e) {
              synchronized (exceptions) {
                exceptions.add(e);
              }
              errors.incrementAndGet();
            } finally {
              endLatch.countDown();
            }
          });
    }

    endLatch.await(60, TimeUnit.SECONDS);
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Async Resolver Race Condition Test ===");
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Resolutions: " + resolutionCount.get());
    System.out.println("Errors: " + errors.get());

    if (!exceptions.isEmpty()) {
      System.out.println("\nFirst 10 exceptions:");
      for (Throwable t : exceptions.subList(0, Math.min(10, exceptions.size()))) {
        System.out.println(t.getClass().getName() + ": " + t.getMessage());
        if (t.getCause() != null) {
          System.out.println("  Cause: " + t.getCause().getClass().getName());
        }
      }
    }

    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Extreme stress test: same Dotprompt, many threads, all hitting resolveTools simultaneously.
   */
  @Test
  public void testExtremeStress() throws Exception {
    int numThreads = 100;
    int iterationsPerThread = 50;

    // Create many registered tools
    Map<String, ToolDefinition> tools = new java.util.HashMap<>();
    for (int i = 0; i < 10; i++) {
      tools.put("tool" + i, new ToolDefinition("tool" + i, "Tool " + i, Map.of(), null));
    }

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CyclicBarrier barrier = new CyclicBarrier(numThreads);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger successfulOps = new AtomicInteger(0);
    AtomicInteger errors = new AtomicInteger(0);

    for (int i = 0; i < numThreads; i++) {
      final int threadId = i;
      executor.submit(
          () -> {
            try {
              barrier.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // Mix of registered and unregistered tools
                  List<String> toolsList = new ArrayList<>();
                  toolsList.add("tool" + ((threadId + j) % 10)); // registered
                  toolsList.add("nonexistent_" + ((threadId + j) % 5)); // unregistered

                  Map<String, Object> config = new java.util.HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  future.get(5, TimeUnit.SECONDS);

                  successfulOps.incrementAndGet();

                } catch (Exception e) {
                  errors.incrementAndGet();
                }
              }
            } catch (Exception e) {
              errors.incrementAndGet();
            } finally {
              endLatch.countDown();
            }
          });
    }

    endLatch.await(60, TimeUnit.SECONDS);
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Extreme Stress Test ===");
    System.out.println("Threads: " + numThreads);
    System.out.println("Iterations per thread: " + iterationsPerThread);
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Successful: " + successfulOps.get());
    System.out.println("Errors: " + errors.get());

    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Test the specific case that might trigger ConcurrentModificationException: iterating over a
   * shared ArrayList while modifications happen.
   *
   * Note: This is actually testing if the ParsedPrompt.tools() list could cause issues. The
   * resolveTools method creates its own ArrayList from the input, so it should be safe.
   */
  @Test
  public void testSharedToolsList() throws Exception {
    int numThreads = 50;
    int iterationsPerThread = 50;

    Map<String, ToolDefinition> tools =
        Map.of("tool1", new ToolDefinition("tool1", "Tool 1", Map.of(), null));

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CyclicBarrier barrier = new CyclicBarrier(numThreads);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);

    // Create a SHARED tools list that all threads use
    List<String> sharedToolsList = new ArrayList<>();
    sharedToolsList.add("tool1");
    sharedToolsList.add("nonexistent");

    for (int i = 0; i < numThreads; i++) {
      executor.submit(
          () -> {
            try {
              barrier.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // All threads use the same config with shared list
                  Map<String, Object> config = new java.util.HashMap<>();
                  config.put("tools", sharedToolsList); // SHARED LIST
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  future.get(5, TimeUnit.SECONDS);

                } catch (Exception e) {
                  errors.incrementAndGet();
                }
              }
            } catch (Exception e) {
              errors.incrementAndGet();
            } finally {
              endLatch.countDown();
            }
          });
    }

    endLatch.await(30, TimeUnit.SECONDS);
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Shared Tools List Test ===");
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Errors: " + errors.get());

    assertThat(errors.get()).isEqualTo(0);
  }
}

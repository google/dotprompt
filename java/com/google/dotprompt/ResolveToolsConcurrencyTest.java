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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * Concurrency test for resolveTools method. This test attempts to trigger race conditions by
 * calling resolveTools/renderMetadata concurrently from multiple threads.
 */
@RunWith(JUnit4.class)
public class ResolveToolsConcurrencyTest {

  /**
   * Test concurrent calls to resolveTools with various configurations. This test attempts to
   * trigger: 1. ConcurrentModificationException on ArrayList 2. Lost updates in shared collections
   * 3. Wrong results due to race conditions
   */
  @Test
  public void testConcurrentResolveTools_noResolver() throws Exception {
    int numThreads = 20;
    int iterationsPerThread = 50;

    // Create shared Dotprompt instance with registered tools
    Map<String, ToolDefinition> tools = new HashMap<>();
    tools.put("tool1", new ToolDefinition("tool1", "Tool 1", Map.of(), null));
    tools.put("tool2", new ToolDefinition("tool2", "Tool 2", Map.of(), null));
    tools.put("tool3", new ToolDefinition("tool3", "Tool 3", Map.of(), null));

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CountDownLatch startLatch = new CountDownLatch(1);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<Throwable> exceptions = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      final int threadId = i;
      executor.submit(
          () -> {
            try {
              // Wait for all threads to be ready
              startLatch.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // Vary the tools list to create different execution paths
                  List<String> toolsList = new ArrayList<>();
                  int toolVariant = (threadId + j) % 4;
                  if (toolVariant >= 0) toolsList.add("tool1");
                  if (toolVariant >= 1) toolsList.add("tool2");
                  if (toolVariant >= 2) toolsList.add("tool3");
                  if (toolVariant >= 3) toolsList.add("nonexistent_tool");

                  Map<String, Object> config = new HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  // Call renderMetadata which internally calls resolveTools
                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(5, TimeUnit.SECONDS);

                  // Verify results are consistent
                  assertThat(metadata).isNotNull();
                  assertThat(metadata.config().get("tools")).isNotNull();
                  assertThat(metadata.config().get("toolDefs")).isNotNull();

                  List<String> resolvedTools = metadata.tools();
                  List<ToolDefinition> toolDefs = metadata.toolDefs();

                  // Verify that registered tools are in toolDefs
                  int expectedToolDefs = 0;
                  for (String tool : toolsList) {
                    if ("tool1".equals(tool) || "tool2".equals(tool) || "tool3".equals(tool)) {
                      expectedToolDefs++;
                    }
                  }
                  // unresolvedTools should contain nonexistent_tool
                  if (toolsList.contains("nonexistent_tool")) {
                    assertThat(resolvedTools).contains("nonexistent_tool");
                  }

                } catch (Exception e) {
                  synchronized (exceptions) {
                    exceptions.add(e);
                  }
                  errors.incrementAndGet();
                }
              }
            } catch (InterruptedException e) {
              Thread.currentThread().interrupt();
            } finally {
              endLatch.countDown();
            }
          });
    }

    // Start all threads at once
    startLatch.countDown();

    // Wait for all threads to complete
    boolean finished = endLatch.await(30, TimeUnit.SECONDS);
    assertThat(finished).isTrue();

    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    // Report results
    System.out.println("=== Test Results ===");
    System.out.println("Threads: " + numThreads);
    System.out.println("Iterations per thread: " + iterationsPerThread);
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Errors: " + errors.get());

    if (!exceptions.isEmpty()) {
      System.out.println("\n=== Exceptions encountered ===");
      for (Throwable t : exceptions) {
        System.out.println(t.getClass().getName() + ": " + t.getMessage());
        if (t.getCause() != null) {
          System.out.println("  Caused by: " + t.getCause().getClass().getName());
        }
      }
    }

    // This assertion will fail if we encounter any real concurrency bugs
    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Test concurrent calls with ToolResolver that has async resolution. This tests the race
   * condition in the synchronized blocks within CompletableFuture callbacks.
   */
  @Test
  public void testConcurrentResolveTools_withResolver() throws Exception {
    int numThreads = 20;
    int iterationsPerThread = 30;

    // Create a tool resolver that returns futures
    ToolResolver mockResolver =
        toolName -> {
          // Simulate async resolution with slight delay
          return CompletableFuture.supplyAsync(
              () -> {
                try {
                  Thread.sleep(1); // Small delay to increase race window
                } catch (InterruptedException e) {
                  Thread.currentThread().interrupt();
                }
                // Only resolve tools with name "dynamic_*"
                if (toolName.startsWith("dynamic_")) {
                  return new ToolDefinition(toolName, "Dynamic tool " + toolName, Map.of(), null);
                }
                return null;
              });
        };

    Map<String, ToolDefinition> staticTools = new HashMap<>();
    staticTools.put("static1", new ToolDefinition("static1", "Static 1", Map.of(), null));
    staticTools.put("static2", new ToolDefinition("static2", "Static 2", Map.of(), null));

    Dotprompt dp =
        new Dotprompt(
            DotpromptOptions.builder().setTools(staticTools).setToolResolver(mockResolver).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CountDownLatch startLatch = new CountDownLatch(1);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<Throwable> exceptions = new ArrayList<>();
    AtomicInteger successfulOps = new AtomicInteger(0);

    for (int i = 0; i < numThreads; i++) {
      final int threadId = i;
      executor.submit(
          () -> {
            try {
              startLatch.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // Create configs with mix of static and dynamic tools
                  List<String> toolsList = new ArrayList<>();

                  // Mix of static and dynamic tools
                  int variant = (threadId + j) % 5;
                  toolsList.add("static1");
                  if (variant >= 1) toolsList.add("static2");
                  if (variant >= 2) toolsList.add("dynamic_tool_a");
                  if (variant >= 3) toolsList.add("dynamic_tool_b");
                  if (variant >= 4) toolsList.add("nonexistent");

                  Map<String, Object> config = new HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(10, TimeUnit.SECONDS);

                  successfulOps.incrementAndGet();

                } catch (Exception e) {
                  synchronized (exceptions) {
                    exceptions.add(e);
                  }
                  errors.incrementAndGet();
                }
              }
            } catch (InterruptedException e) {
              Thread.currentThread().interrupt();
            } finally {
              endLatch.countDown();
            }
          });
    }

    startLatch.countDown();
    boolean finished = endLatch.await(60, TimeUnit.SECONDS);
    assertThat(finished).isTrue();

    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Test with Resolver Results ===");
    System.out.println("Threads: " + numThreads);
    System.out.println("Iterations per thread: " + iterationsPerThread);
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Successful: " + successfulOps.get());
    System.out.println("Errors: " + errors.get());

    if (!exceptions.isEmpty()) {
      System.out.println("\n=== Exceptions ===");
      for (Throwable t : exceptions) {
        System.out.println(t.getClass().getName() + ": " + t.getMessage());
        if (t.getCause() != null) {
          System.out.println("  Caused by: " + t.getCause().getClass().getName());
        }
      }
    }

    assertThat(errors.get()).isEqualTo(0);
  }

  /**
   * Test specifically targeting the unsynchronized add at line 552. This test tries to trigger the
   * race condition when toolResolver and store are both null.
   */
  @Test
  public void testConcurrentResolveTools_targetLine552() throws Exception {
    int numThreads = 30;
    int iterationsPerThread = 100;

    // Create Dotprompt without resolver or store
    Map<String, ToolDefinition> tools = new HashMap<>();
    tools.put("tool1", new ToolDefinition("tool1", "Tool 1", Map.of(), null));

    Dotprompt dp =
        new Dotprompt(
            DotpromptOptions.builder()
                .setTools(tools)
                // No toolResolver, no store - path goes through line 552
                .build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CountDownLatch startLatch = new CountDownLatch(1);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger concurrentModificationErrors = new AtomicInteger(0);
    List<Throwable> allExceptions = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      executor.submit(
          () -> {
            try {
              startLatch.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // Create config with mix of existent and nonexistent tools
                  List<String> toolsList = new ArrayList<>();
                  toolsList.add("tool1"); // exists
                  toolsList.add("nonexistent_" + j); // doesn't exist - goes to line 552

                  Map<String, Object> config = new HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  PromptMetadata metadata = future.get(5, TimeUnit.SECONDS);

                } catch (Exception e) {
                  allExceptions.add(e);
                  if (e.getCause() instanceof java.util.ConcurrentModificationException
                      || e instanceof java.util.ConcurrentModificationException) {
                    concurrentModificationErrors.incrementAndGet();
                  }
                }
              }
            } catch (InterruptedException e) {
              Thread.currentThread().interrupt();
            } finally {
              endLatch.countDown();
            }
          });
    }

    startLatch.countDown();
    boolean finished = endLatch.await(30, TimeUnit.SECONDS);
    assertThat(finished).isTrue();

    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== Test Line 552 (unsynchronized add) Results ===");
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("ConcurrentModificationExceptions: " + concurrentModificationErrors.get());
    System.out.println("Total exceptions: " + allExceptions.size());

    for (Throwable t : allExceptions) {
      System.out.println("Exception: " + t.getClass().getName() + ": " + t.getMessage());
    }

    // If we hit a real ConcurrentModificationException, this test proves the bug
    assertThat(concurrentModificationErrors.get()).isEqualTo(0);
  }

  /**
   * Stress test with high contention - all threads trying to resolve the same tool names
   * simultaneously.
   */
  @Test
  public void testConcurrentResolveTools_highContention() throws Exception {
    int numThreads = 50;
    int iterationsPerThread = 20;

    Map<String, ToolDefinition> tools = new HashMap<>();
    for (int i = 0; i < 5; i++) {
      tools.put("tool" + i, new ToolDefinition("tool" + i, "Tool " + i, Map.of(), null));
    }

    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().setTools(tools).build());

    ExecutorService executor = Executors.newFixedThreadPool(numThreads);
    CountDownLatch startLatch = new CountDownLatch(1);
    CountDownLatch endLatch = new CountDownLatch(numThreads);

    AtomicInteger errors = new AtomicInteger(0);
    List<String> errorMessages = new ArrayList<>();

    for (int i = 0; i < numThreads; i++) {
      executor.submit(
          () -> {
            try {
              startLatch.await();

              for (int j = 0; j < iterationsPerThread; j++) {
                try {
                  // All threads use the same tool list - high contention
                  List<String> toolsList = List.of("tool0", "tool1", "nonexistent");
                  Map<String, Object> config = new HashMap<>();
                  config.put("tools", toolsList);
                  ParsedPrompt parsedPrompt =
                      ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

                  CompletableFuture<PromptMetadata> future = dp.renderMetadata(parsedPrompt);
                  future.get(5, TimeUnit.SECONDS);

                } catch (Exception e) {
                  synchronized (errorMessages) {
                    errorMessages.add(e.getClass().getName() + ": " + e.getMessage());
                  }
                  errors.incrementAndGet();
                }
              }
            } catch (InterruptedException e) {
              Thread.currentThread().interrupt();
            } finally {
              endLatch.countDown();
            }
          });
    }

    startLatch.countDown();
    boolean finished = endLatch.await(30, TimeUnit.SECONDS);
    assertThat(finished).isTrue();

    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.SECONDS);

    System.out.println("=== High Contention Test Results ===");
    System.out.println("Threads: " + numThreads);
    System.out.println("Iterations per thread: " + iterationsPerThread);
    System.out.println("Total operations: " + (numThreads * iterationsPerThread));
    System.out.println("Errors: " + errors.get());

    if (!errorMessages.isEmpty()) {
      System.out.println("\nFirst 10 error messages:");
      errorMessages.stream().limit(10).forEach(System.out::println);
    }

    assertThat(errors.get()).isEqualTo(0);
  }
}

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

package com.google.dotprompt.store;

import com.google.dotprompt.models.DeletePromptOrPartialOptions;
import com.google.dotprompt.models.ListPartialsOptions;
import com.google.dotprompt.models.ListPromptsOptions;
import com.google.dotprompt.models.LoadPartialOptions;
import com.google.dotprompt.models.LoadPromptOptions;
import com.google.dotprompt.models.PaginatedPartials;
import com.google.dotprompt.models.PaginatedPrompts;
import com.google.dotprompt.models.PartialRef;
import com.google.dotprompt.models.PromptData;
import com.google.dotprompt.models.PromptRef;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Synchronous filesystem-based prompt store implementation.
 *
 * <p>Reads and writes prompts and partials from/to the local file system within a specified
 * directory using synchronous operations.
 *
 * <h2>File Naming Conventions</h2>
 *
 * <ul>
 *   <li>Prompts: {@code [name][.variant].prompt}
 *   <li>Partials: {@code _[name][.variant].prompt}
 * </ul>
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * DirStoreSync store = new DirStoreSync(DirStoreOptions.of("/path/to/prompts"));
 *
 * // List prompts
 * PaginatedPrompts prompts = store.list(null);
 *
 * // Load a specific prompt
 * PromptData data = store.load("my_prompt", null);
 *
 * // Save a prompt
 * store.save(new PromptData("new_prompt", null, null, "---\nmodel: gemini\n---\nHello"));
 * }</pre>
 */
public class DirStoreSync implements PromptStoreWritableSync {

  private final Path directory;

  /**
   * Creates a new DirStoreSync instance.
   *
   * @param options Configuration options including the base directory.
   */
  public DirStoreSync(DirStoreOptions options) {
    this.directory = options.directory();
  }

  @Override
  public PaginatedPrompts list(ListPromptsOptions options) {
    try {
      List<String> files = StoreUtils.scanDirectory(directory);
      List<PromptRef> prompts = new ArrayList<>();

      for (String relativePath : files) {
        String filename = Path.of(relativePath).getFileName().toString();
        if (StoreUtils.isPartial(filename)) {
          continue;
        }

        StoreUtils.ParsedFilename parsed = StoreUtils.parsePromptFilename(filename);
        Path filePath = directory.resolve(relativePath);
        String content = Files.readString(filePath, StandardCharsets.UTF_8);
        String version = StoreUtils.calculateVersion(content);

        // Include subdirectory in the name
        String dirPart =
            relativePath.contains("/") || relativePath.contains("\\")
                ? relativePath.substring(0, relativePath.lastIndexOf(filename))
                : "";
        String fullName = dirPart + parsed.name();
        // Normalize path separators
        fullName = fullName.replace('\\', '/');
        if (fullName.endsWith("/")) {
          fullName = fullName.substring(0, fullName.length() - 1) + "/" + parsed.name();
        } else if (!dirPart.isEmpty()) {
          fullName = dirPart.replace('\\', '/') + parsed.name();
        } else {
          fullName = parsed.name();
        }

        prompts.add(new PromptRef(fullName, parsed.variant(), version));
      }

      return new PaginatedPrompts(prompts, null);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  @Override
  public PaginatedPartials listPartials(ListPartialsOptions options) {
    try {
      List<String> files = StoreUtils.scanDirectory(directory);
      List<PartialRef> partials = new ArrayList<>();

      for (String relativePath : files) {
        String filename = Path.of(relativePath).getFileName().toString();
        if (!StoreUtils.isPartial(filename)) {
          continue;
        }

        StoreUtils.ParsedFilename parsed = StoreUtils.parsePromptFilename(filename);
        Path filePath = directory.resolve(relativePath);
        String content = Files.readString(filePath, StandardCharsets.UTF_8);
        String version = StoreUtils.calculateVersion(content);

        // Include subdirectory in the name
        String dirPart = "";
        if (relativePath.contains("/") || relativePath.contains("\\")) {
          int idx = Math.max(relativePath.lastIndexOf('/'), relativePath.lastIndexOf('\\'));
          dirPart = relativePath.substring(0, idx + 1).replace('\\', '/');
        }
        String fullName = dirPart + parsed.name();

        partials.add(new PartialRef(fullName, parsed.variant(), version));
      }

      return new PaginatedPartials(partials, null);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  @Override
  public PromptData load(String name, LoadPromptOptions options) {
    String variant = options != null ? options.variant() : null;
    String requestedVersion = options != null ? options.version() : null;

    String filename = StoreUtils.buildFilename(name, variant, false);
    Path filePath = directory.resolve(filename);

    try {
      String content = Files.readString(filePath, StandardCharsets.UTF_8);
      String version = StoreUtils.calculateVersion(content);

      if (requestedVersion != null && !requestedVersion.equals(version)) {
        throw new IllegalArgumentException(
            "Version mismatch: requested " + requestedVersion + " but found " + version);
      }

      return new PromptData(name, variant, version, content);
    } catch (NoSuchFileException e) {
      throw new UncheckedIOException(
          new IOException("Prompt not found: " + name + (variant != null ? "." + variant : "")));
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  @Override
  public PromptData loadPartial(String name, LoadPartialOptions options) {
    String variant = options != null ? options.variant() : null;
    String requestedVersion = options != null ? options.version() : null;

    String filename = StoreUtils.buildFilename(name, variant, true);
    Path filePath = directory.resolve(filename);

    try {
      String content = Files.readString(filePath, StandardCharsets.UTF_8);
      String version = StoreUtils.calculateVersion(content);

      if (requestedVersion != null && !requestedVersion.equals(version)) {
        throw new IllegalArgumentException(
            "Version mismatch: requested " + requestedVersion + " but found " + version);
      }

      return new PromptData(name, variant, version, content);
    } catch (NoSuchFileException e) {
      throw new UncheckedIOException(
          new IOException("Partial not found: " + name + (variant != null ? "." + variant : "")));
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  @Override
  public void save(PromptData prompt) {
    if (prompt.name() == null || prompt.name().isEmpty()) {
      throw new IllegalArgumentException("Prompt name is required");
    }
    if (prompt.source() == null) {
      throw new IllegalArgumentException("Prompt source is required");
    }

    // Determine if this is a partial (name starts with _)
    boolean isPartial = prompt.name().startsWith("_");
    String name = isPartial ? prompt.name().substring(1) : prompt.name();

    String filename = StoreUtils.buildFilename(name, prompt.variant(), isPartial);
    Path filePath = directory.resolve(filename);

    try {
      Files.createDirectories(filePath.getParent());
      Files.writeString(filePath, prompt.source(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  @Override
  public void delete(String name, DeletePromptOrPartialOptions options) {
    String variant = options != null ? options.variant() : null;

    // Try deleting as a prompt first
    String promptFilename = StoreUtils.buildFilename(name, variant, false);
    Path promptPath = directory.resolve(promptFilename);

    if (Files.exists(promptPath)) {
      try {
        Files.delete(promptPath);
        return;
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }

    // Try deleting as a partial
    String partialFilename = StoreUtils.buildFilename(name, variant, true);
    Path partialPath = directory.resolve(partialFilename);

    if (Files.exists(partialPath)) {
      try {
        Files.delete(partialPath);
        return;
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }

    throw new UncheckedIOException(
        new IOException(
            "Neither prompt nor partial found: " + name + (variant != null ? "." + variant : "")));
  }
}

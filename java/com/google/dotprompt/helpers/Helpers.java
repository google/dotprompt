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

package com.google.dotprompt.helpers;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.util.DefaultIndenter;
import com.fasterxml.jackson.core.util.DefaultPrettyPrinter;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Options;
import java.io.IOException;

/**
 * Standard Handlebars helpers for Dotprompt.
 *
 * <p>This class registers and implements helpers for:
 *
 * <ul>
 *   <li>JSON serialization ({@code json})
 *   <li>Media markers ({@code media})
 *   <li>Role markers ({@code role})
 *   <li>History injection ({@code history})
 *   <li>Section delineation ({@code section})
 *   <li>Equality checks ({@code ifEquals}, {@code unlessEquals})
 * </ul>
 */
public class Helpers {

  private static final ObjectMapper mapper = new ObjectMapper();

  /**
   * Registers all standard Dotprompt helpers with the given Handlebars instance.
   *
   * @param handlebars The Handlebars instance to register helpers with.
   */
  public static void register(Handlebars handlebars) {
    handlebars.registerHelper("json", Helpers::json);
    handlebars.registerHelper("media", Helpers::media);
    handlebars.registerHelper("role", Helpers::role);
    handlebars.registerHelper("history", Helpers::history);
    handlebars.registerHelper("section", Helpers::section);
    handlebars.registerHelper("ifEquals", Helpers::ifEquals);
    handlebars.registerHelper("unlessEquals", Helpers::unlessEquals);
  }

  /**
   * Serializes an object to a JSON string.
   *
   * <p>Usage: {{json object [indent=2]}}
   *
   * @param context The context object (used if no parameter is provided).
   * @param options The Handlebars options, including indentation settings.
   * @return The JSON string representation.
   * @throws IOException If serialization fails.
   */
  public static Object json(Object context, Options options) throws IOException {
    Object target = (options.params.length > 0) ? options.param(0) : context;

    ObjectMapper localMapper = mapper;

    Integer indent = options.hash("indent", null);
    if (indent != null) {
      DefaultPrettyPrinter printer =
          new DefaultPrettyPrinter();
      printer.indentObjectsWith(new DefaultIndenter("  ", "\n"));

      localMapper =
          mapper
              .copy()
              .setDefaultPrettyPrinter(
                  new DefaultPrettyPrinter() {
                    @Override
                    public DefaultPrettyPrinter createInstance() {
                      return new DefaultPrettyPrinter(this) {
                        @Override
                        public void writeObjectFieldValueSeparator(
                            JsonGenerator g) throws IOException {
                          g.writeRaw(": ");
                        }
                      };
                    }

                    @Override
                    public void writeObjectFieldValueSeparator(
                        JsonGenerator g) throws IOException {
                      g.writeRaw(": ");
                    }
                  })
              .enable(SerializationFeature.INDENT_OUTPUT);
    }

    return localMapper.writeValueAsString(target);
  }

  /**
   * Renders a media marker for multimedia content.
   *
   * <p>Usage: {{media url="http://..." contentType="image/png"}}
   *
   * @param context The context object (unused).
   * @param options The Handlebars options containing url and contentType.
   * @return A dotprompt media marker string.
   * @throws IOException If JSON serialization of the payload fails.
   */
  public static Object media(Object context, Options options) throws IOException {
    String url = options.hash("url", "");
    String contentType = options.hash("contentType", "");

    if (url.isEmpty()) {
      return "";
    }

    StringBuilder sb = new StringBuilder("<<<dotprompt:media:url ");
    sb.append(url);
    if (!contentType.isEmpty()) {
      sb.append(" ").append(contentType);
    }
    sb.append(">>>");
    return sb.toString();
  }

  /**
   * Renders a role marker to switch the message role.
   *
   * <p>Usage: {{role "user"}} or {{#role "user"}}...{{/role}}
   *
   * @param context The role name (if used as block or single arg).
   * @param options The Handlebars options.
   * @return A dotprompt role marker string.
   */
  public static Object role(Object context, Options options) {
    if (options.params.length > 0) {
      return "<<<dotprompt:role:" + options.param(0) + ">>>";
    }
    if (context instanceof String) {
      return "<<<dotprompt:role:" + context + ">>>";
    }
    return "";
  }

  /**
   * Renders a history marker to insert conversation history.
   *
   * <p>Usage: {{history}}
   *
   * @param context The context object (unused).
   * @param options The Handlebars options.
   * @return A dotprompt history marker string.
   */
  public static Object history(Object context, Options options) {
    return "<<<dotprompt:history>>>";
  }

  /**
   * Renders a section marker.
   *
   * <p>Usage: {{section "name"}}
   *
   * @param context The section name.
   * @param options The Handlebars options.
   * @return A dotprompt section marker string.
   */
  public static Object section(Object context, Options options) {
    if (options.params.length > 0) {
      return "<<<dotprompt:section " + options.param(0) + ">>>";
    }
    if (context instanceof String) {
      return "<<<dotprompt:section " + context + ">>>";
    }
    return "";
  }

  /**
   * Renders the block if two values are equal.
   *
   * <p>Usage: {{#ifEquals value1 value2}}...{{/ifEquals}}
   *
   * @param context The first value (or context if params are shifted).
   * @param options The Handlebars options containing the second value.
   * @return The rendered block or inverse.
   * @throws IOException If rendering fails.
   */
  public static Object ifEquals(Object context, Options options) throws IOException {
    Object arg0 = context;
    Object arg1 = null;

    if (options.params.length == 0) {
      return options.inverse(context);
    } else if (options.params.length == 1) {
      arg0 = context;
      arg1 = options.param(0);
    } else {
      arg0 = options.param(0);
      arg1 = options.param(1);
    }

    boolean equals = strictEquals(arg0, arg1);

    if (equals) {
      return options.fn(context);
    } else {
      return options.inverse(context);
    }
  }

  /**
   * Renders the block unless two values are equal.
   *
   * <p>Usage: {{#unlessEquals value1 value2}}...{{/unlessEquals}}
   *
   * @param context The first value.
   * @param options The Handlebars options containing the second value.
   * @return The rendered block or inverse.
   * @throws IOException If rendering fails.
   */
  public static Object unlessEquals(Object context, Options options) throws IOException {
    Object arg0 = context;
    Object arg1 = null;

    if (options.params.length == 0) {
      return options.fn(context);
    } else if (options.params.length == 1) {
      arg0 = context;
      arg1 = options.param(0);
    } else {
      arg0 = options.param(0);
      arg1 = options.param(1);
    }

    boolean equals = strictEquals(arg0, arg1);

    if (!equals) {
      return options.fn(context);
    } else {
      return options.inverse(context);
    }
  }

  /**
   * Performs a strict equality check between two objects.
   *
   * @param arg0 The first object.
   * @param arg1 The second object.
   * @return True if objects are equal, false otherwise.
   */
  private static boolean strictEquals(Object arg0, Object arg1) {
    if (arg0 == null) return arg1 == null;
    if (arg1 == null) return false;
    return arg0.equals(arg1);
  }
}

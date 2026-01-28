/**
 * Copyright 2024 Google LLC
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
 */

import { getCollection } from "astro:content";
import Fuse, { type FuseResult, type IFuseOptions } from "fuse.js";
import { useState, useMemo, useEffect } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

import { Search as SearchIcon } from "lucide-react";

import type { DocsEntry } from "@/lib/types";
import { capitalizeFirstLetter } from "@/lib/utils";

function extractHeaders(body: string): string[] {
  const headers = [];
  const lines = body.split("\n");
  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.*)/);
    if (match) {
      headers.push(match[2]);
    }
  }
  return headers;
}

const docs: DocsEntry[] = await getCollection("docs");

const options: IFuseOptions<DocsEntry> = {
  includeScore: true,
  threshold: 0.5,
  location: 0,
  distance: 100,
  includeMatches: true,
  minMatchCharLength: 2,
  useExtendedSearch: true,
  findAllMatches: true,
  keys: [
    { name: "id", weight: 2.5 },
    { name: "slug", weight: 2.5 },
    { name: "body", weight: 1 },
    {
      name: "title",
      weight: 2,
      getFn: (docs: DocsEntry) => docs.data.title,
    },
    {
      name: "description",
      weight: 1.75,
      getFn: (docs: DocsEntry) => docs.data.description || "",
    },
    {
      name: "tags",
      weight: 1.5,
      getFn: (docs: DocsEntry) => docs.data.tags.join(" ") || "",
    },
    {
      name: "headers",
      weight: 2,
      getFn: (docs: DocsEntry) => extractHeaders(docs.body).join(" "),
    },
  ],
};

export function Search() {
  const [open, setOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const fuse: Fuse<DocsEntry> = useMemo(() => new Fuse(docs, options), [docs]);
  const results: FuseResult<DocsEntry>[] = useMemo(
    () => fuse.search(searchValue),
    [fuse, searchValue],
  );

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <div className="">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button size="icon" variant="ghost">
            <SearchIcon className="w-[1.2rem] h-[1.2rem]" />
          </Button>
        </DialogTrigger>
        <DialogContent className="md:h-1/2 md:mx-0 w-full h-full">
          <DialogHeader>
            <DialogTitle hidden={true}>Search</DialogTitle>
            <DialogDescription asChild className="relative">
              <div className="mt-6 flex flex-col">
                <Input
                  placeholder="Search ..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                />
                {results.length > 0 && (
                  <ScrollArea className="relative md:max-h-dynamic_search mt-4">
                    <ul className="list-none m-0">
                      {results.map(({ item, refIndex }) => (
                        <li
                          className=" px-4 m-0 py-2 flex flex-row items-center hover:rounded text-foreground bg-background hover:text-primary-foreground hover:bg-primary"
                          key={refIndex}
                        >
                          <a
                            href={`/dotprompt/${item.slug}`}
                            key={refIndex}
                            className=" no-underline hover:text-primary-foreground"
                          >
                            {item.data.title
                              ? capitalizeFirstLetter(item.data.title)
                              : capitalizeFirstLetter(item.slug.split("/")[-1])}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </ScrollArea>
                )}
              </div>
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </div>
  );
}

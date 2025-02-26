import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

const base54Chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

export function generateUniqueId(length: number): string {
  let result = "";
  for (let i = 0; i < length; i++) {
    result += base54Chars.charAt(Math.floor(Math.random() * base54Chars.length));
  }
  return result;
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

# **Packaging Rust for Python**

This repository contains a Handlebars implementation for Python, based on the Rust Handlebars library. Below are the steps to package this implementation for PyPI publishing.

## **Compatibility Requirements**

This project needs to be compatible with PyPI on the following platforms and architectures:

* **Linux**: `arm64` & `x86_64`

* **Windows**: `x86_64`

* **macOS**: `arm64` & `x86_64`

## **Docker Extensions for Cross-Compilation**

To simulate an `arm64` architecture from `x86_64` machines, we use two Docker extensions:

### **1\. [Docker Buildx](https://github.com/docker/buildx)**

Buildx is a Docker extension that provides advanced features for building multi-platform container images. It allows building Docker images for different architectures (e.g., `arm64` and `x86_64`) from a single build environment.

For more details, check the [official Docker documentation](https://docs.docker.com/reference/cli/docker/buildx/).

### **2\. [QEMU](https://www.qemu.org/)**

QEMU is an open-source emulator and virtualizer that enables cross-platform compatibility. It allows running and building applications for different architectures (like ARM or PowerPC) on a host machine with a different architecture (like `x86_64`).

---

These extensions are integrated using the following dedicated GitHub Actions:

* [docker/setup-qemu-action](https://github.com/docker/setup-qemu-action)

* [docker/setup-buildx-action](https://github.com/docker/setup-buildx-action)

## **Rust Tools for Cross-Compilation**

We use [Rustup](https://rustup.rs/) for managing the Rust toolchain. Rustup allows you to install, update, and manage multiple Rust versions and associated tools.

### **Important Tools**

* **Cargo**: Rust’s package manager and build system, used for managing dependencies, compiling code, running tests, and building packages. [Learn more about Cargo](https://github.com/rust-lang/cargo).

* **LLVM-tools**: A set of utilities for working with compiled languages, essential for generating cross-platform and cross-architecture Python wheels, particularly for Windows. The `llvm-tools` component is also installed with rustup, enabling the creation of cross-platform wheels, including those for Windows. For more details on cross-compiling for Windows, see [this guide](https://www.maturin.rs/distribution.html#cross-compile-to-windows).

### **Target Architectures for Compilation**

Those are the target platforms added with rustup for cross compilation:

* **arm64**:

  * `aarch64-unknown-linux-gnu`

  * `aarch64-apple-darwin` (macOS)

  * `aarch64-unknown-linux-gnu-msl` (alpine)

* **x86\_64**:

  * `x86_64-unknown-linux-gnu`

  * `x86_64-pc-windows-msvc` (Windows)

  * `x86_64-apple-darwin` (macOS)


## **Required Packages & Libraries**

To compile the Rust and Python components, the following packages are required:

### **Rust-side Dependencies**

* [**PyO3**](https://pyo3.rs/v0.24.0/): A Rust crate that allows you to write native Python extensions in Rust, providing bindings between Python and Rust.

### **Python-side Dependencies**

* [**Maturin**](https://www.maturin.rs/index.html): A tool for building Python packages with Rust extensions, making it easier to create Python wheels for Rust code.

* [**Ziglang**](https://www.maturin.rs/distribution.html#cross-compile-to-linuxmacos): A package to facilitate building Python wheels for macOS, especially when dealing with cross-compilation.

These tools must be installed to compile the Python wheels and cross-compile for macOS.

## **Important Variables to Consider**

### **1\. Python Version**

You must specify the Python interpreter version for which the wheel will be built. For example, when building for Python 3.12, use the following command:

```
maturin build --release --target aarch64-unknown-linux-gnu -i python3.12
```

The resulting wheel file will be named like:

```
handlebarrz-0.1.0-cp312-cp312-musllinux_1_2_aarch64.whl
```

In the file name, `cp312` indicates compatibility with CPython 3.12. If you need to build for a different Python version (e.g., 3.13), rerun the command with the new version.

### **2\. glibc Version (Linux)**

glibc (GNU C Library) is essential for system libraries and functions required by C and C++ programs on Linux. While Rust doesn't directly rely on glibc, the Python wheels need to be compatible with the glibc version on the target system.

For example, when building for Linux `x86_64`, the command is:

```
maturin build --release --target x86_64-unknown-linux-gnu -i python3.12
```

The resulting wheel file will be named like:

```
handlebarrz-0.1.0-cp312-cp312-manylinux_2_28_x86_64.whl
```

Here, `manylinux_2_28` specifies the glibc version. If you need compatibility with a different version of glibc, rerun the command with these additional flags to specify compatibility:

```
maturin build --release --target x86_64-unknown-linux-gnu -i python3.12 --compatibility manylinux_2_40 --auditwheel=skip
```




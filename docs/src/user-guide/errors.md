# How to: handle errors

Every call that can fail returns `Result<T, seams::Error>`. `Error` has
three variants:

| Variant | When |
| --- | --- |
| `Library { status, message }` | The engine refused the call with a status the crate names. `message` says why in words. |
| `Other { code, message }` | The engine returned a status code that this version of the crate does not name. |
| `Argument { message }` | The value could not be passed to the engine at all, such as a path with a nul byte or a coordinate list whose length is not a multiple of 3. |

Three methods read an error without matching on it. `status()` is `Some`
only for `Library`. `code()` is the integer status, and an `Argument`
error has code 4. `message()` is the text. `Display` prints the message
followed by the status name.

## The statuses

| Status | Code | Meaning |
| --- | --- | --- |
| `Ok` | 0 | The call succeeded. |
| `Null` | 1 | A required pointer was null. |
| `Range` | 2 | A number was outside the accepted range. |
| `Cell` | 3 | The cell is missing or has no volume. |
| `Argument` | 4 | An argument had the wrong shape. |
| `State` | 5 | The handle has no frame yet. |
| `Memory` | 6 | An allocation failed. |
| `Internal` | 7 | The engine hit an internal failure. |

## Matching on a failure

An empty frame has nothing to classify, so `chill_plus` returns
`Status::State`. A cage signature search on a cell thinner than twice the
cutoff is refused with `Status::Argument`, and the message explains why.

```rust
use seams::{ChillOptions, SignatureOptions, Status, System};

fn main() -> Result<(), seams::Error> {
    let mut empty = System::new()?;
    let err = empty.chill_plus(&ChillOptions::default()).unwrap_err();
    assert_eq!(err.status(), Some(Status::State));
    println!("{err}");

    let (xyz, edge) = seams::diamond8();
    let mut thin = System::new()?;
    thin.set_ortho(&xyz, edge, edge, edge)?;
    let err = thin
        .signature_cages(&SignatureOptions::default())
        .err()
        .expect("a thin cell is refused");
    assert_eq!(err.status(), Some(Status::Argument));
    println!("{}", err.message());
    Ok(())
}
```

```text
system has no frame (no frame)
cage search refused: the cell is thinner than twice the neighbour cutoff, so one pair can meet through more than one periodic image
```

`Error` implements `std::error::Error`, so `?` converts it into
`Box<dyn Error>` and into `anyhow::Error`.

## Handles and ownership

`System`, `Neighbours`, `Rings`, `Cages`, `Fingerprint` and `Brine` each own
a native object. Moving a handle moves that ownership, and dropping it frees
the object. The raw pointer is not part of the public API, so there is
nothing to free by hand.

A handle is `Send` but not `Sync`. The engine requires exclusive use of one
handle, so move a handle to another thread rather than sharing it. Two
frames on two threads may run `steinhardt`, `ql`, `q4q6` or `q6bar` at the
same time.

## Threads

`set_num_threads(n)` sets the OpenMP width for the next call. It is
process-global, so do not call it while another thread is inside the
library. `0` restores the library default. `num_threads()` reads the width
the next call will use.

```rust
fn main() -> Result<(), seams::Error> {
    seams::set_num_threads(1)?;
    println!("threads {}", seams::num_threads());
    Ok(())
}
```

```text
threads 1
```

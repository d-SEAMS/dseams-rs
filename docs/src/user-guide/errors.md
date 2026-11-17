# How to: handle errors

Fallible calls return `Result<T, seams::Error>`. `Error` is one of three
variants.

| Variant | When |
| --- | --- |
| `Library { status, message }` | The C call failed with a status this crate names. `message` is `seams_handle_error` for that handle. |
| `Other { code, message }` | The library returned a status code this crate does not name. |
| `Argument { message }` | The value cannot cross the C boundary, such as a nul inside a path, or a coordinate slice whose length is not a multiple of 3. |

`status()` is `Some` only for `Library`. `code()` is the status integer.
An `Argument` uses code 4. `message()` is the detail text. `Display`
prints the message and the status name.

An empty system has no frame. `chill_plus` then returns `Status::State`:

```rust
fn main() -> Result<(), seams::Error> {
    let mut system = seams::System::new()?;
    let err = system
        .chill_plus(&seams::ChillOptions::default())
        .expect_err("an empty frame has no coordinates");
    assert_eq!(err.status(), Some(seams::Status::State));
    assert_eq!(err.code(), seams::Status::State as i32);
    Ok(())
}
```

The named statuses, and their integer values, are `Ok` (0), `Null` (1),
`Range` (2), `Cell` (3), `Argument` (4), `State` (5), `Memory` (6), and
`Internal` (7).

## Ownership

`System`, `Neighbours`, `Rings`, `Cages`, `Fingerprint`, and `Brine`
own their C pointers. Moving a handle moves that ownership. Dropping it
calls the matching destroy function. The raw pointer is not part of the
public API.

A handle is `Send`. It is not `Sync`: the C library requires exclusive
use of one handle. Two frames on two threads may run `steinhardt`, `ql`,
`q4q6`, or `q6bar` at the same time. `set_num_threads` is process-global.
Do not call it while another thread is inside the library. Zero restores
the library default. `num_threads` reads the width the next call will use.

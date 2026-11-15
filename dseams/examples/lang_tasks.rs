// Copyright (c) d-SEAMS developers
//! Neighbours, rings, and CHILL+ from Rust.
//!
//! The same ice Ih census runs in every language front of d-SEAMS and prints
//! one line. Each library call is a `Result`, and `Drop` frees the system,
//! the neighbour list and the ring set. `cargo run --example lang_tasks
//! [dump]` reads `tests/data/ice1h.lammpstrj` when no path is given.
use seams::{ChillOptions, Error, NeighbourOptions, RingOptions, System};
use std::env;

const FIXTURE: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/data/ice1h.lammpstrj");

/// The line every language front prints for `ice1h.lammpstrj`.
#[cfg(test)]
const CANON: &str = "pairs 512 rings 0 0 0 0 0 0 256 chill 0 128 0 0 0 0 0 0 0";

fn joined(values: &[i32]) -> String {
    values
        .iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(" ")
}

fn census(path: &str) -> Result<String, Error> {
    let mut frame = System::new()?;
    frame.read(path, 1, -1)?;
    let pairs = frame.neighbours(&NeighbourOptions::default())?.nnz()?;
    let rings = frame
        .rings(&RingOptions {
            max_size: 6,
            ..RingOptions::default()
        })?
        .histogram(6)?;
    let chill = frame.chill_plus(&ChillOptions::default())?;
    Ok(format!(
        "pairs {pairs} rings {} chill {}",
        joined(&rings),
        joined(&chill.counts)
    ))
}

fn main() -> Result<(), Error> {
    let path = env::args().nth(1).unwrap_or_else(|| FIXTURE.to_string());
    println!("{}", census(&path)?);
    Ok(())
}

#[test]
fn matches_the_other_language_fronts() {
    seams::set_num_threads(1).unwrap();
    assert_eq!(census(FIXTURE).unwrap(), CANON);
}

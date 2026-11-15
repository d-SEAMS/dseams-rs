// Copyright (c) d-SEAMS developers
//! Ice Ih census through the safe seams crate.
//!
//! `cargo run --example ice_ih [dump]` reads `tests/data/ice1h.lammpstrj`
//! when no path is given.
use seams::{ChillOptions, Label, System};
use std::env;

const FIXTURE: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/tests/data/ice1h.lammpstrj");

fn census(path: &str) -> String {
    let mut system = System::new().expect("system");
    system.read(path, 1, 1).expect("read");
    let n = system.count();
    let order = system.q4q6(3.5).expect("q6");
    let mean = order.q6.iter().sum::<f64>() / order.q6.len() as f64;
    let ice = system.chill_plus(&ChillOptions::default()).expect("chill+");
    let (six, _fraction) = system.six_ring_fraction(3.5).expect("rings");
    format!(
        "rust ice nop {} q6 {:.6} hexagonal {} rings {}",
        n,
        mean,
        ice.counts[Label::Hexagonal as usize],
        six
    )
}

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| FIXTURE.to_string());
    println!("{}", census(&path));
}

#[test]
fn ice_ih_census() {
    assert_eq!(
        census(FIXTURE),
        "rust ice nop 128 q6 0.625855 hexagonal 128 rings 256"
    );
}

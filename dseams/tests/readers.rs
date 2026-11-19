/* Copyright (c) d-SEAMS developers */
use std::path::PathBuf;

fn fixture(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/data")
        .join(name)
}

fn read_count(name: &str) -> i32 {
    let mut system = seams::System::new().unwrap();
    system.read(fixture(name).to_str().unwrap(), 1, -1).unwrap();
    system.count()
}

#[test]
fn reads_con_with_readcon() {
    if !seams::has_readcon() {
        eprintln!("skipped: readcon-core is not in this build");
        return;
    }
    assert_eq!(read_count("tiny.con"), 2);
}

#[test]
fn reads_pdb_with_chemfiles() {
    if !seams::has_chemfiles() {
        eprintln!("skipped: chemfiles is not in this build");
        return;
    }
    assert_eq!(read_count("tiny.pdb"), 2);
}

#[test]
fn reads_gro_with_chemfiles() {
    if !seams::has_chemfiles() {
        eprintln!("skipped: chemfiles is not in this build");
        return;
    }
    assert_eq!(read_count("tiny.gro"), 2);
}

#[test]
fn required_readers_are_present() {
    if std::env::var_os("DSEAMS_REQUIRE_READERS").is_some() {
        assert!(seams::has_chemfiles());
        assert!(seams::has_readcon());
    }
}

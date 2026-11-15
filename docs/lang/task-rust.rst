Rust
====

Each library call returns a ``Result``, and ``Drop`` frees the system, the
neighbour list and the ring set. The printed histograms are the ring-size
and CHILL+ label counts.

.. literalinclude:: ../../dseams/examples/lang_tasks.rs
   :language: rust

``cargo run --example lang_tasks`` runs it on ``dseams/tests/data/ice1h.lammpstrj``
and prints the line every d-SEAMS language front prints::

   pairs 512 rings 0 0 0 0 0 0 256 chill 0 128 0 0 0 0 0 0 0

``cargo test --examples`` checks that line.

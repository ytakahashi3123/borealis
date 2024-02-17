# Borealis

Bayesian optimization for finding realizable solutions for discretized equation


# Code description

`Borealis` solves an inverse problem based on the Bayesian optimization.


# How to start calculation

## Execution

```console
python3 src/borealis.py
```

Tutorial case: `testcase/work`

## Configuration file

Optimization by `Borealis` is controled by the configuration file: `borealis.yml`.

## External code

When an external code, for example, `Tcode`, is used, the pass needs to be specified in `borealis.yml`.

## Requirements

`Borealis` requires the following packages:

- numpy (>=1.22.3)
- yaml (>= 5.3.1)
- GPyOpt (>= 1.2.6)


# Contact:

Yusuke Takahashi, Hokkaido University

ytakahashi@eng.hokudai.ac.jp


# Date:

2024/2/29


# References

- Yusuke Takahashi, Masahiro Saito, Nobuyuki Oshima, and Kazuhiko Yamada, “Trajectory Reconstruction for Nanosatellite in Very Low Earth Orbit Using Machine Learning.” Acta Astronautica 194: 301–8. 2022. https://doi.org/https://doi.org/10.1016/j.actaastro.2022.02.010.

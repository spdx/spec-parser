# main script called on the command-line

# SPDX-License-Identifier: Apache-2.0

from spec_parser import Model
from runparams import RunParams

if __name__ == "__main__":
    cfg = RunParams()
    # TODO: process args in RunParams() -- for now, hardwired values outside
    indir = "/home/zvr/github/spdx/spdx-3-model/model"
    outdir = "/tmp/specout"

    m = Model(indir)
    m.gen_all(outdir, cfg)


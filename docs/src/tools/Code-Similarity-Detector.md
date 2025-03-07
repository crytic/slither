`slither-simil` uses state-of-the-art machine learning to detect similar (vulnerable) Solidity functions. We have provided a pretrained model from [etherscan_verified_contracts](https://github.com/thec00n/etherscan_verified_contracts) with 60,000 contracts and more than 850,000 functions to get you started quickly. We included the capability to easily train new models if you have access to larger or different datasets.

`slither-simil` uses [FastText](https://github.com/facebookresearch/fastText), a vector embedding technique, to generate compact numerical representations of every function. We used FastText because it:

* implements several state-of-the-art techniques such as nbow and skipgrams,
* has high performance (it is C++ code with Python bindings),
* has MIT license, and
* is well maintained (by Facebook).
 
## Requirements

Install the required packages before using `slither-simil`:

```
$ pip3 install pybind11 --user
$ pip3 install https://github.com/facebookresearch/fastText/archive/0.2.0.zip --user
$ pip3 install sklearn matplotlib --user # for plot mode
```

Make sure that you are using `pip3.6` or later. If you are running from inside a [virtualenv](https://virtualenv.pypa.io/en/latest/), remove the `--user` parameter.

## Usage

Note that these examples will use the following files:

* [etherscan_verified_contracts.bin](https://drive.google.com/file/d/1oEhbIL4V9582Y5VKp4iiOURGq8qa4cBN/view?usp=sharing)
* [cache.npz](https://drive.google.com/file/d/1vpwusbyzLn1JqqAvlFivHXtLvsEp0VqX/view?usp=sharing)
* [MetaCoin.sol](https://github.com/crytic/slither/wiki/MetacoinExample)

`slither-simil` has three modes:
- `test` - finds similar functions to your own in a dataset of contracts
- `plot` - provide a visual representation of similarity of multiple sampled functions
- `train` - builds new models of large datasets of contracts
- `info` - inspects the internal information of the pre-trained model or the assessed code

### Test mode

This mode transforms a function into a vector and uses it to find similar functions.

Test mode requires the following parameters: 
1. A pre-trained model: this file will be used to transform every function into a vector, you can [train your own](#train-mode) or [use our pre-trained one (etherscan_verified_contracts.bin)](#usage).
2. A contract filename: this file will contain the code that you want to compare,
3. A function name (e.g. `SafeMath.add` or `add`), 
4. An input directory or file: this can be either a directory with contracts or a [cache file with a pre-computed list of vectors for every contract (cache.npz)](#usage).

Use the cache to avoid long processing times to compile and vectorize the input contracts.  

Here's an example that finds functions similar to `sendCoin` in `MetaCoin` (compiled with `solc-0.4.25`). Searching for similar functions among more than 800,000 functions takes only 20 seconds.

```
$ slither-simil test etherscan_verified_contracts.bin --filename MetaCoin.sol --fname MetaCoin.sendCoin --input cache.npz --ntop 25 --solc solc-0.4.25
INFO:Slither-simil:Reviewed 825062 functions, listing the 25 most similar ones:
INFO:Slither-simil:filename                                                          contract             function             score     
INFO:Slither-simil:0x954b5de09a55e59755acbda29e1eb74a45d30175_Fluz.sol               Fluz                 transfer             1.0       
INFO:Slither-simil:0x55648de19836338549130b1af587f16bea46f66b_Pebbles.sol            Pebbles              transfer             1.0       
INFO:Slither-simil:0x3fcee23add6e86dde3c4d395cbce1cae7f16d06d_SnipCoin.sol           SnipCoin             sendCoin             1.0       
INFO:Slither-simil:0x000000005fbe2cc9b1b684ec445caf176042348e_ProperProposal.sol     Vote                 transfer             1.0       
INFO:Slither-simil:0x000000002bb43c83ece652d161ad0fa862129a2c_AccountRegistry.sol    Vote                 transfer             1.0       
INFO:Slither-simil:0x4e84e9e5fb0a972628cf4568c403167ef1d40431_Fluzcoin.sol           Fluzcoin             transfer             1.0       
INFO:Slither-simil:0x334eec1482109bd802d9e72a447848de3bcc1063_AirDropToken.sol       AirDropToken         transfer             1.0       
INFO:Slither-simil:0x28ccdda197d319a241005b9c9f01bac48b90f556_AirDropToken.sol       AirDropToken         transfer             1.0       
INFO:Slither-simil:0x000000002647e16d9bab9e46604d75591d289277_Vote.sol               Vote                 transfer             1.0       
INFO:Slither-simil:0xc6c4c7826D44ABF22c711E8E86bDC3f5242d2182_token.sol              token                sendCoin             1.0       
INFO:Slither-simil:0x22033df1d104736ff4c2b23a28affe52863ca9c8_AtmOnlyFluzcoin.sol    AtmOnlyFluzcoin      transfer             1.0       
INFO:Slither-simil:0xcad796d6a2c0bb1de7f24262819be96fb08c1c3a_Love.sol               Love                 transfer             1.0       
INFO:Slither-simil:0x6cb2b8dc6a508c9a21db9683d1a729715969a6ee_TokenEscrow.sol        TokenEscrow          transferFromOwner    0.996     
INFO:Slither-simil:0xd75fefe3cdb647281eec3f8fc738e3bc9658f9e4_ProofOfReadToken.sol   ProofOfReadToken     transfer             0.996     
INFO:Slither-simil:0x7A8Ef7E8c8f16B9D6F39069ce03d752Af23b46d6_OBS_V1.sol             MyObs                transfer             0.996     
INFO:Slither-simil:0x5ac0197c944c961f58bb02f3d0df58a74fdc15b6_TokenEscrow.sol        TokenEscrow          transferFromOwner    0.996     
INFO:Slither-simil:0x69719c8c207036bdfc3632ccc24b290fb7240f4a_BitPayToken.sol        BitPayToken          transfer             0.996     
INFO:Slither-simil:0x3d8a10ce3228cb428cb56baa058d4432464ea25d_TestToken.sol          TestToken            transfer             0.993     
INFO:Slither-simil:0x69719c8c207036bdfc3632ccc24b290fb7240f4a_BitPayToken.sol        BitPayToken          transferFrom         0.992     
INFO:Slither-simil:0x486e1f44b2a85150a6dd2de5aab87df375cd8880_CAIRToken.sol          StandardToken        transfer             0.991     
INFO:Slither-simil:0x2bec16b164725efc192b7ec0296f838c61317514_eda.sol                StandardToken        transfer             0.991     
INFO:Slither-simil:0xb7cb1c96db6b22b0d3d9536e0108d062bd488f74_WaltonToken.sol        StandardToken        transfer             0.991     
INFO:Slither-simil:0x346c3be6aebEBaF5Cb766a75aDc9827EfbB7E41A_DelphiToken.sol        StandardToken        transfer             0.991     
INFO:Slither-simil:0xf5068761511594c82328102f4fde4650ed9ea6c4_WHP.sol                WHP                  transfer             0.991     
INFO:Slither-simil:0x5f9f2ae7150d0beef3bb50ac8d8f4b43e6a6cc57_NABC.sol               NABC                 transfer             0.991     
```

### Train mode

Train mode trains new models used to vectorize functions. You will need a large amount of contracts/functions if you plan to train a new model.

```
$ slither-simil train model.bin --input contracts
INFO:Slither-simil:Saving extracted data into last_data_train.txt
INFO:Slither-simil:Starting training
Read 0M words
Number of words:  348
Number of labels: 0
Progress: 100.0% words/sec/thread:   53124 lr:  0.000000 loss:  2.066949 ETA:   0h 0m
INFO:Slither-simil:Training complete
INFO:Slither-simil:Saving model
INFO:Slither-simil:Saving cache in cache.npz
INFO:Slither-simil:Done!
```

After it runs, the `slither-simil` will output the the trained model in `model.bin`, a cache of every function for use in test mode in `cache.npz`, and the SlithIR of every function for debugging in `last_data_train.txt`.

### Plot mode

Plot mode plots sets of functions to visually detect clusters of similar ones.

Here's an example to plot all the functions named `add` from contracts named `SafeMath` sampling from 500 random contracts:

```
$ slither-simil plot etherscan_verified_contracts.bin --fname SafeMath.add --input cache.npz --nsamples 500 
INFO:Slither-simil:Loading data..
INFO:Slither-simil:Procesing data..
INFO:Slither-simil:Plotting data..
INFO:Slither-simil:Saving figure to plot.png..
```

![plot](https://user-images.githubusercontent.com/31542053/57525857-3d794f80-7302-11e9-9677-b4eb3f6a5c20.png)

This mode performs dimensionality reduction using PCA, so the axes you see here [are **not** associated with any particular unit](https://stats.stackexchange.com/questions/137813/the-meaning-of-units-on-the-axes-of-a-pca-plot). 

It can can be also used to plot sets of functions using only a name from any contract (e.g. `burn`) .

### Info mode

This mode has two features. You can inspect the internal information about a pre-trained model. Info mode is typically used for debugging.

```
$ slither-simil info etherscan_verified_contracts.bin 
INFO:Slither-simil:etherscan_verified_contracts.bin uses the following words:
INFO:Slither-simil:</s>
INFO:Slither-simil:index(uint256)
INFO:Slither-simil:return
INFO:Slither-simil:condition(temporary_variable)
INFO:Slither-simil:member
INFO:Slither-simil:solidity_call(require(bool))
INFO:Slither-simil:library_call
INFO:Slither-simil:binary(+)
INFO:Slither-simil:event
INFO:Slither-simil:(local_solc_variable(default)):=(temporary_variable)
...
```

... or examine the internal representation of function:

```
$ slither-simil info etherscan_verified_contracts.bin --filename MetaCoin.sol --fname MetaCoin.sendCoin --solc solc-0.4.25
INFO:Slither-simil:Function sendCoin in contract MetaCoin is encoded as:
INFO:Slither-simil:index(uint256) binary(<) condition(temporary_variable) return index(uint256) binary(-) index(uint256) binary(+) event return
INFO:Slither-simil:[ 0.00689753 -0.05349572 -0.06854086 -0.01667773  0.1259813  -0.05974023
  0.06719872 -0.04520541  0.13745852  0.14690697 -0.03721125  0.00579037
  0.06865194 -0.03804035  0.01224702 -0.1014601  -0.02655532 -0.15334933
...
```
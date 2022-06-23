const { types } = require("@algo-builder/web");

const appId = 96684192
const appAddr = 'NLSIGFGXSIRXYJC6YERMY7Z6RWCVREKE3UAW6W3V75EHOJYHULUSJ6M52Q'

async function run(runtimeEnv, deployer) {

    let url = "str:ipfs://belandi"
    let metadata = "str:besughi"

    const buyer = deployer.accountsByName.get("buyer")
    const admin = deployer.accountsByName.get("admin")

    let amount = 9000
    let fund = 2e6
    await deployer.executeTx(
        [
            {
                type: types.TransactionType.TransferAlgo,
                sign: types.SignType.SecretKey,
                fromAccount: admin,
                toAccountAddr: appAddr,
                amountMicroAlgos: fund,
                payFlags: {totalFee: 4000} 
            }
        ]
    )

    let tx1 =  {
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: buyer,
        appID: appId,
        payFlags: {totalFee: 0},
        appArgs: ["str:buy",url, metadata],
    }

    let tx2 = {
        type: types.TransactionType.TransferAlgo,
        sign: types.SignType.SecretKey,
        fromAccount: buyer,
        toAccountAddr: appAddr,
        amountMicroAlgos: amount,
        payFlags: {totalFee: 4000}
     }

    
    
     console.log(buyer)
    let txGroup = [tx1, tx2]
    await deployer.executeTx(txGroup)
/*
    await deployer.executeTx(
        {
            type: types.TransactionType.CallApp,
            sign: types.SignType.SecretKey,
            fromAccount: buyer.account,
            appID: appId,
            payFlags: {totalFee: 1000},
            appArgs: ["str:claim"],
            foreignAssets: [parseInt(await readAppLocalState(deployer, buyer.addr, appId))]
        }
    
    )

    */
}

module.exports = {default: run};


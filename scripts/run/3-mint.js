const { types } = require("@algo-builder/web");


async function run(runtimeEnv, deployer) {

    let url = "str:ipfs://Qmey46LyR31EAeSMtroAdhxhkf2uKnqZUeJRWqWDfYJcoj"
    let metadata = "str:besughi"

    const buyer = deployer.accountsByName.get("buyer")
    const admin = deployer.accountsByName.get("admin")

    const App = await deployer.getApp("dinoMinter");
    const appId = App.appID
    const appAddr = App.applicationAccount

    let amount = 90000
    
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

}

module.exports = {default: run};


const { types } = require("@algo-builder/web");
const { readAppLocalState } = require("@algo-builder/algob");

const appId = 96684192

async function run(runtimeEnv, deployer) {
    const admin = deployer.accountsByName.get("admin");
    const buyer = deployer.accountsByName.get("buyer");



    let state = await readAppLocalState(deployer, buyer.addr, appId)
    assetID = state.get('unclaimed')

    await deployer.executeTx(
        {
            type: types.TransactionType.OptInASA,
            sign: types.SignType.SecretKey,
            fromAccount: buyer,
            assetID: assetID,
            payFlags: {totalFee: 1000},
        }
    
    )



    await deployer.executeTx(
        {
            type: types.TransactionType.CallApp,
            sign: types.SignType.SecretKey,
            fromAccount: buyer,
            appID: appId,
            payFlags: {totalFee: 1000},
            appArgs: ["str:claim"],
            foreignAssets: [assetID]
        }
    
    )


}

module.exports = {default: run};

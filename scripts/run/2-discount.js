const { types } = require("@algo-builder/web");


async function run(runtimeEnv, deployer) {
    let accounts = deployer.accounts;
    
    const App = await deployer.getApp("dinoMinter");
    const appId = App.appID

    const admin = accounts[0];
    const buyer = accounts[1];

    await deployer.executeTx({
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: admin,
        appID: appId,
        payFlags: {totalFee: 1000},
        appArgs: ["str:give_discount"],
        accounts: [buyer.addr],
    }
);
}

module.exports = {default: run};

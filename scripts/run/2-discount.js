const { types } = require("@algo-builder/web");

const appId = 96684192

async function run(runtimeEnv, deployer) {
    let accounts = deployer.accounts;

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

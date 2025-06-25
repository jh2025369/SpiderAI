function getXDsPowResponse(e, t) {
    return btoa(JSON.stringify({
        algorithm: e.algorithm,
        challenge: e.challenge,
        salt: e.salt,
        answer: e.answer,
        signature: e.signature,
        target_path: t
    }));
}

// res = getXDsPowResponse({
//     algorithm: 'DeepSeekHashV1',
//     challenge: '0a4ac8757d8a0be5089d702ac081ea1f93f60096bc24c2085be6625f17667704',
//     salt: '753a9c8f0f561d2cb842',
//     answer: 51881,
//     signature: '427768c2331117e2e5cf2f407bb67ec7adb4437c9c4eb93326daec92a23b6a60',
// }, '/api/v0/file/upload_file')
// console.log(res);
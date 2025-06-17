const commonUtil = require('./libs/miaoshou/common.js');

function loginParam(mobile, password) {
    let formData = {
        mobile: mobile.trim(),
        password: password,
    };

    formData.mobile = commonUtil.aesEncrypt(formData.mobile);
    formData.password = commonUtil.aesEncrypt(formData.password);
    formData.isVerifyRemoteLogin = true;
    
    return formData;
}
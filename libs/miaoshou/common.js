const CryptoJS = require('./crypto.js');
const $ = require('./jquery.js');

var commonUtil = {
  toast: undefined,
  mobileScreenWidthLimit: 768,
  showToast: function(message, duration = 2 * 1000){
    commonUtil.toast.innerHTML = message;
    commonUtil.toast.classList.add('toast-active');

    var toastTimer = setTimeout(function () {
      commonUtil.toast.classList.remove('toast-active');

      toastTimer = null;
    }, duration);

    return toastTimer;
  },

  getCountdownMsg: function (countdownSec) {
    return countdownSec + '秒后重新获取';
  },

  codeCountdown: function ($btn, finishCallback) {
    var text = $btn.text();
    // 请求成功开始倒计时
    $btn.addClass('disabled');
    var countdownSec = 60;
    $btn.text(commonUtil.getCountdownMsg(countdownSec));

    var codeMsgTimer = null;
    var invoke = function () {
      countdownSec--;
      if (countdownSec <= 0) {
        clearInterval(codeMsgTimer);
        finishCallback && finishCallback();

        codeMsgTimer = null;
        $btn.data('codeTimer', null)
            .removeClass('disabled')
            .text(text);
      } else {
        $btn.text(commonUtil.getCountdownMsg(countdownSec))
      }
    };
    invoke();
    codeMsgTimer = setInterval(invoke, 1000);
  },

  getFormData: function(dom) {
    var formData = {};
    $(dom).find('.J_inputField').each(function() {
      var key = $(this).attr('name');
      formData[key] = $(this).val();
    });

    return formData;
  },

  isMobile: function() {
    return window.screen.width <= this.mobileScreenWidthLimit;
    // if(window.navigator.userAgent.match(/(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i)) {
    //   return true; // 移动端
    // }else{
    //   return false; // PC端
    // }
  },

  getAesKey: function () {
    var charAtCodes = [
      64, 51,  52,  51,  56, 106,
      106, 59, 115, 105, 100, 117,
      102, 56,  51,  50
    ];
    var chars = [];
    for (var i = 0; i < charAtCodes.length; i++) {
      chars.push(String.fromCharCode(charAtCodes[i]));
    }
    return chars.join('');
  },

  aesEncrypt: function (content) {
    try {
      const srcs = CryptoJS.enc.Utf8.parse(content)
      const key = CryptoJS.enc.Utf8.parse(commonUtil.getAesKey())
      const iv = CryptoJS.enc.Utf8.parse("")

      const encrypted = CryptoJS.AES.encrypt(srcs, key, {
        iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      })

      return encrypted.toString();
    } catch (e) {
      return content;
    }
  },
  aesDecrypt: function (content) {
    var iv = '';
    try {
      const secretKey = CryptoJS.enc.Utf8.parse(commonUtil.getAesKey());
      const secretIv = CryptoJS.enc.Utf8.parse(iv);
      const result = CryptoJS.AES.decrypt(content, secretKey, {
        iv: secretIv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7,
      });
      return result.toString(CryptoJS.enc.Utf8);
    } catch (e) {
      return content;
    }
  },
};

module.exports = commonUtil;
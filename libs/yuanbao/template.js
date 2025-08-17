XMLHttpRequest = require('xhr2');
FormData = require('form-data');
React = require('react');
WebSocket = require('ws');

const { JSDOM } = require('jsdom');
const { createCanvas } = require('canvas');
responses = {};

const dom = new JSDOM(`
    <!DOCTYPE html>
    <html>
        <body>
            <div id="app"></div>
        </body>
    </html>
    `,
    {
        url: 'https://yuanbao.tencent.com/',
    }
);
self = window = dom.window;
document = window.document;
Node = window.Node;
localStorage = window.localStorage;
sessionStorage = window.sessionStorage;
addEventListener = window.addEventListener;
Event = window.Event;
CustomEvent = window.Event;
MutationObserver = window.MutationObserver;
HTMLAnchorElement = window.HTMLAnchorElement;
getComputedStyle = window.getComputedStyle;

cancelAnimationFrame = (id) => {};

window.XMLHttpRequest = XMLHttpRequest;
function createXHRInterceptor() {
    const originalOpen = XMLHttpRequest.prototype.open;
	const originalSetHeader = XMLHttpRequest.prototype.setRequestHeader;
	const originalSend = XMLHttpRequest.prototype.send;
  
	return {
		install() {
			XMLHttpRequest.prototype.open = function(method, url) {
				// 存储原始URL（供后续参考）
				this._originalUrl = url;

                const baseUrl = new URL('https://yuanbao.tencent.com');
                const parsedUrl = new URL(url, baseUrl);
				
				// 判断是否需要代理
				if (!url.includes('https')) {
				// 拼接代理IP和端口
					parsedUrl.protocol = 'https:';
					parsedUrl.hostname = 'https://yuanbao.tencent.com';
					parsedUrl.port = '';
					
					console.log(`[Proxy] 原始URL: ${url} → 代理URL: ${parsedUrl.href}`);

					// 存储修改后的URL
					this._modifiedUrl = parsedUrl.href;
				}
				
				// 调用原始open方法
				return originalOpen.call(this, method, parsedUrl.href);
			};

            XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
                if (value === undefined) {
                    return;
                }
                originalSetHeader.call(this, name, value);
            };

			XMLHttpRequest.prototype.send = function(body) {
				this.onload = function() {
					console.log('[Interceptor] Response:', this.responseText);
                    responses[this._url.href] = this.responseText;
				};

				console.log(`[${new Date().toISOString()}] XHR Request:`, { 
					url: this._url.href, 
					method: this._method 
				});

                if (body instanceof FormData) {
                    body = body.getBuffer();
                }

                this._headers['cookie'] = document.cookie;
				
				originalSend.call(this, body);
			};
		}
	};
}
// 使用拦截器
const interceptor = createXHRInterceptor();
interceptor.install();

window.HTMLCanvasElement.prototype.getContext = function(type) {
    if (type === '2d') {
        // 使用 node-canvas 创建真实的 Canvas 上下文
        const canvas = createCanvas(this.width || 300, this.height || 150);
        return canvas.getContext('2d');
    }
    return null;
};

// 添加 toDataURL 支持
window.HTMLCanvasElement.prototype.toDataURL = function() {
    const canvas = createCanvas(this.width, this.height);
    return canvas.toDataURL();
};

window.matchMedia = (query) => ({
    matches: false, // 默认不匹配
    media: query,
    addListener: () => {}, // 空函数
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
});

CSS = {
    supports: (prop, value) => {
        const supportedFeatures = {
        'display': ['flex', 'grid', 'block'],
        'position': ['sticky', 'fixed']
        };
        
        return supportedFeatures[prop]?.includes(value) ?? false;
    },
    escape: (ident) => CSS.escape(ident) // 可选添加其他方法
};

IntersectionObserver = class MockIntersectionObserver {
    constructor() {}
    observe() {}
    unobserve() {}
    disconnect() {}
};

screen = {
    width: 1536,
    height: 864
}

performance.timing = {
    domInteractive: 0,
    domLoading: 0,
    loadEventStart: 0
}

navigator = {
    userAgent: "Mozilla/5.0",
    webdriver: false,
    languages: ['zh-CN', 'zh'],
    platform: 'Win32',
    cookieEnabled: true
};
window.navigator = navigator;

location = {
    host: 'yuanbao.tencent.com',
    hostname: 'yuanbao.tencent.com',
    protocol: 'https:',
    href: 'https://yuanbao.tencent.com/chat/naQivTmsDa',
    pathname: "/chat/naQivTmsDa"
};


let dirPath = './static';
if (!__dirname.includes('libs\\yuanbao')) {
    dirPath = './libs/yuanbao/static';
}

function requireCommonJSModule() {
    /* AUTO_IMPORTS */
}


function set_cache(agent_id, cookie) {
    location.href = `https://yuanbao.tencent.com/chat/${agent_id}`;
    location.pathname = `/chat/${agent_id}`;

    cookie.split('; ').forEach(cookie => {
        document.cookie = cookie;
    });
}

function get_header() {
    let header = {};
    let newHeader = {};
    runtime.t[45718].exports.f8("/api/chat/", header);
    newHeader['x-bus-params-md5'] = header['X-Bus-Params-Md5'].toString();
    newHeader['x-timestamp'] = header['X-Timestamp'].toString();
    newHeader['x-uskey'] = header['X-Uskey'];
    setTimeout(() => {
        process.exit();
    }, 3000);
    return newHeader;
}

async function get_user_info() {
    let res = await runtime.t[18025].exports.A.request({
        url: "/api/getuserinfo",
        method: "get"
    });
    return res;
}

async function chat(prompt, chat_id, current_index = 0) {
    let message =  "";

    if (!chat_id) {
        const res = await runtime.t[18025].exports.A.request({
            url: "/api/user/agent/conversation/create",
            method: "post",
            data: {
                agentId: "naQivTmsDa"
            }
        })

        chat_id = res.data.id;
    }

    supportFunctions = ['autoInternetSearch', 'openInternetSearch', 'closeInternetSearch'];
    chatModelId = ['deep_seek_v3', 'deep_seek'];
    options = {
        'backendUpdateFlag': 2,
        'intentionStatus': true,
        'needIntentionModel': true
    }
    data = {
        'agentId': 'naQivTmsDa',
        'chatModelId': 'deep_seek_v3',
        'displayPromptType': 1,
        // 'hintParentAnswerIndex': 0,
        // 'hintParentIndex': 2,
        // 'hintPromptTraceId': "b69f06f07ae14898af1be6bcc2fffb1f_0",
        'isAtomInput': false,
        'model': 'gpt_175B_0404',
        'options': options,
        'plugin': 'Adaptive',
        'Prompt': prompt,
        'skillId': 'unique-skill-aisearch',
        'supportFunctions': ['autoInternetSearch'],
        'supportHint': 1,
        'version': 'v2',
    }
    const res = await runtime.t[18025].exports.A.request({
        url: `/api/chat/${chat_id}`,
        method: "post",
        data
    })
    return res;

    // return new Promise(resolve => {
    //     runtime.t[54633].exports.F({
    //         traceId: Math.random().toString(16).slice(2),
    //         url: `/api/chat/${chat_id}`,
    //         data: {
    //             agentId: "naQivTmsDa",
    //             chatModelId: "deep_seek_v3",
    //             displayPrompt: prompt,
    //             model: "gpt_175B_0404",
    //             plugin: "Adaptive",
    //             prompt,
    //         },
    //         headers: {
    //             lastSpeechIdx: 0,
    //             currentIndex: current_index        // 聊天记录数 * 2
    //         },
    //         headers: {},
    //         timeout: 6e4,
    //         onData: (e) => {
    //             message += e.content.msg;
    //         },
    //         onEnd: (e) => {
    //             resolve(true);
    //         },
    //         onError: () => null,
    //         onTimeout: () => null,
    //         onPlugin: () => null,
    //         onMsgIdx: () => null,
    //         onExtra: () => null,
    //         onDelete: () => null,
    //     })
    // }).then(() => {
    //     return message;
    // });
}

set_cache('naQivTmsDa', cookie);
requireCommonJSModule();
get_user_info();
// get_header();
// chat("v8引擎内核提取");
/*
 * html-template-card — patched
 * ----------------------------
 * 原实现（205261230102）的问题：processAndRender() 每次实体变化都会新建一个
 * render_template WS 订阅，且从不退订。镜像页引用 ~60 个实体、每 5s 刷新一次，
 * 订阅数会无限累积，最终把浏览器压垮（整页闪烁 / 空白 / 加载不出来）。
 *
 * 本补丁：
 *  1. 模板是静态的，订阅一次就够 —— render_template 订阅本身会在输出变化时持续推送。
 *  2. rAF 合并渲染，同一帧内的多次推送只写一次 DOM。
 *  3. 元素移除时退订，避免切换视图后残留订阅。
 *  4. shouldUpdate() 对已被删除的实体做空值保护（原版会抛异常）。
 */
class HtmlTemplateCard extends HTMLElement {
    static get properties() {
        return {
            _config: {},
            _hass: {},
        };
    }

    set hass(hass) {
        const oldHass = this._hass;
        this._hass = hass;
        if (this._config && this._hass && !this._entities) {
            this.calculateEntites();
        }
        if (!oldHass || this.shouldUpdate(oldHass)) {
            this.processAndRender();
        }
    }

    shouldUpdate(oldHass) {
        if (!this._entities || !this._entities.length) return true;
        if (this._config.always_update) return true;
        return this._entities.some((entity) => {
            const a = oldHass.states[entity];
            const b = this._hass.states[entity];
            if (!a || !b) return a !== b;
            return a.state !== b.state || a.attributes !== b.attributes;
        });
    }

    setConfig(config) {
        if (!config.content) {
            throw new Error("You need to define 'content' in your configuration.")
        }
        this._config = config;
        if (this._config && this._hass && !this._entities) {
            this.calculateEntites();
        }
        if (!this._config.picture_elements_mode) {
            let haCard = document.createElement("ha-card");
            haCard.style.padding = "16px";
            this._rootElement = haCard;
        } else {
            this._rootElement = document.createElement("div");
        }
    }

    calculateEntites() {
        this._entities = [];
        if (this._config.entities && Array.isArray(this._config.entities)) {
            for (const entity in this._config.entities) {
                this._entities.push(this._config.entities[entity]);
            }
        }
        for (const entity in this._hass.states) {
            if (this._config.content.includes(entity)) {
                this._entities.push(this._hass.states[entity].entity_id);
            }
        }
    }

    processAndRender() {
        // 订阅只建一次；后续变化由 HA 侧订阅推送，不再重复订阅。
        if (this._subscribed) return;

        let content = this._config.content;
        if (!this._config.ignore_line_breaks) {
            content = content.replace(/\r?\n|\r/g, "</br>");
        }
        this._subscribed = true;
        if (!this._config.do_not_parse) {
            this._subPromise = this._hass.connection.subscribeMessage(
                (msg) => this.render(msg.result),
                { type: "render_template", template: content }
            );
        } else {
            this.render(content);
        }
        if (!(this._rootElement in this.children)) {
            this.appendChild(this._rootElement);
        }
    }

    render(content) {
        // 同一帧内的多次推送合并成一次 DOM 写入，避免重复重排造成的闪烁。
        this._pending = content;
        if (this._raf) return;
        this._raf = requestAnimationFrame(() => {
            this._raf = null;
            this._apply(this._pending);
        });
    }

    _apply(content) {
        let header = ``;
        if (this._config.title) {
            header = `<div class="card-header" style="padding: 8px 0 16px 0;"><div class="name">${this._config.title}</div></div>`;
        }
        this._rootElement.innerHTML = this._config.picture_elements_mode
            ? content
            : `${header}<div>${content}</div>`;
    }

    disconnectedCallback() {
        if (this._subPromise) {
            this._subPromise.then((unsub) => unsub()).catch(() => { });
        }
        this._subPromise = null;
        this._subscribed = false;
        if (this._raf) {
            cancelAnimationFrame(this._raf);
            this._raf = null;
        }
    }

    getCardSize() {
        return 1;
    }
}

customElements.define('html-template-card', HtmlTemplateCard);

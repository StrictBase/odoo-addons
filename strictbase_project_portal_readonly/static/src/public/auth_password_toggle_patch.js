import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

class StrictBaseAuthPasswordTogglePatch extends Interaction {
    static selector = ".input-group";
    static selectorHas = ":scope > .o_show_password";

    setup() {
        this.onToggleClick = () => queueMicrotask(() => this.syncButton());
    }

    start() {
        this.inputEl = this.el.querySelector("input[type='password'], input[type='text']");
        this.buttonEl = this.el.querySelector(".o_show_password");
        this.iconEl = this.buttonEl?.querySelector("i");
        if (!this.inputEl || !this.buttonEl || !this.iconEl) {
            return;
        }
        this.buttonEl.addEventListener("click", this.onToggleClick);
        this.observer = new MutationObserver(() => this.syncButton());
        this.observer.observe(this.inputEl, { attributes: true, attributeFilter: ["type"] });
        this.syncButton();
    }

    destroy() {
        this.buttonEl?.removeEventListener("click", this.onToggleClick);
        this.observer?.disconnect();
    }

    syncButton() {
        if (!this.inputEl || !this.buttonEl || !this.iconEl) {
            return;
        }
        const isVisible = this.inputEl.type === "text";
        this.iconEl.classList.toggle("fa-eye", isVisible);
        this.iconEl.classList.toggle("fa-eye-slash", !isVisible);
        this.buttonEl.setAttribute("title", isVisible ? "Hide password" : "Show password");
        this.buttonEl.setAttribute("aria-label", isVisible ? "Hide password" : "Show password");
    }
}

registry.category("public.interactions").add("strictbase.auth_password_toggle_patch", StrictBaseAuthPasswordTogglePatch);

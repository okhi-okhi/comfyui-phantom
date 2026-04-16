import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "Phantom.A1111PromptParser",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "PhantomA1111PromptParser") {

      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) onNodeCreated.apply(this, arguments);

        setTimeout(() => {
          const pop_widget = this.widgets.find((w) => w.name === "populated_text");
          const mode_widget = this.widgets.find((w) => w.name === "mode");

          if (pop_widget && mode_widget) {
            pop_widget.inputEl.placeholder = "Populated Prompt (Generated automatically)";

            const updateState = (val) => {
              if (val === "populate") {
                pop_widget.inputEl.disabled = true;
                pop_widget.inputEl.style.opacity = "0.6";
              } else {
                pop_widget.inputEl.disabled = false;
                pop_widget.inputEl.style.opacity = "1.0";
              }
            };

            updateState(mode_widget.value);

            const originalComboSet = Object.getOwnPropertyDescriptor(mode_widget.constructor.prototype, "value")?.set;

            let _value = mode_widget.value;
            Object.defineProperty(mode_widget, "value", {
              set: (val) => {
                _value = val;
                updateState(val);
                if (originalComboSet) originalComboSet.call(mode_widget, val);
              },
              get: () => _value || "populate"
            });
          }
        }, 10);
      };

      const onExecuted = nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted = function (message) {
        if (onExecuted) onExecuted.apply(this, arguments);

        if (this.widgets && message.string && message.string.length > 0) {
          const pop_widget = this.widgets.find((w) => w.name === "populated_text");
          const in_widget = this.widgets.find((w) => w.name === "wildcard_text");

          // Just show current prompt
          if (pop_widget) pop_widget.value = message.string[0];
          if (in_widget && message.wildcard && message.wildcard.length > 0) {
            in_widget.value = message.wildcard[0];
          }
        }
      };
    }
  }
});
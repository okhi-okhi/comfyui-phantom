import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
  name: "Phantom.A1111PromptParser",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "PhantomA1111PromptParser") {
      const onExecuted = nodeType.prototype.onExecuted;

      nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, arguments);

        if (this.widgets && message.text) {
          const text_value = message.text.join("");

          // Target the text box widget or create it
          let widget = this.widgets.find((w) => w.name === "parsed_result");
          if (!widget) {
            widget = ComfyWidgets["STRING"](this, "parsed_result", ["STRING", { multiline: true }], app).widget;

            // Force it to be strictly read-only visually and functionally
            widget.inputEl.readOnly = true;
            widget.inputEl.style.backgroundColor = "#222"; // Darker background to look disabled
            widget.inputEl.style.color = "#ccc"; // Dimmer text
            widget.inputEl.style.opacity = "0.8";

            // Allow selecting text for copying, but disable editing
            widget.inputEl.addEventListener("keydown", (e) => {
              if (e.key !== "c" && e.key !== "C" && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
              }
            });

            this.setSize(this.computeSize());
          }

          // Update read-only widget text safely
          widget.value = text_value;
        }
      };
    }
  }
});
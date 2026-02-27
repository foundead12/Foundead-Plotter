from flask import Flask, render_template, request, send_file
import sympy as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import io, base64

app = Flask(__name__)

# Global variable to hold the last plot data
last_plot_data = None

def clean_function_input(function_str):
    function_str = function_str.lower()
    replacements = {
        "cosx": "cos(x)",
        "sinx": "sin(x)",
        "tanx": "tan(x)",
        "logx": "log(x)",   # natural log
        "lnx": "ln(x)",     # alias for log
        "sqrtx": "sqrt(x)",
        "absx": "abs(x)",
        "exp(x)": "exp(x)"  # exponential
    }
    for wrong, right in replacements.items():
        function_str = function_str.replace(wrong, right)
    function_str = function_str.replace("^", "**")  # allow x^2 notation
    return function_str

@app.route("/", methods=["GET", "POST"])
def home():
    global last_plot_data
    plot_url = None
    error_message = None

    if request.method == "POST":
        if "clear" in request.form:  # Clear Plot button pressed
            last_plot_data = None
            return render_template("index.html", plot_url=None, error_message=None)

        function_str = request.form["function"]
        try:
            functions = [f.strip() for f in function_str.split(",")]

            # Get ranges
            x_min = float(request.form.get("x_min", -10))
            x_max = float(request.form.get("x_max", 10))
            y_min = float(request.form.get("y_min", -10))
            y_max = float(request.form.get("y_max", 10))

            # Get interval spacing (default None)
            x_interval = request.form.get("x_interval")
            y_interval = request.form.get("y_interval")

            graph_title = request.form.get("graph_title", f"Plot of {', '.join(functions)}")
            x_label = request.form.get("x_label", "x")
            y_label = request.form.get("y_label", "f(x)")

            custom_labels = request.form.get("labels", "")
            custom_labels = [lbl.strip() for lbl in custom_labels.split(",")] if custom_labels else []

            x = sp.symbols("x")
            X = np.linspace(x_min, x_max, 400)

            plt.figure()
            colors = ["blue", "red", "green", "orange", "purple", "brown"]
            styles = ["-", "--", "-.", ":"]

            for i, func in enumerate(functions):
                func = clean_function_input(func)
                expr = sp.sympify(func)
                f = sp.lambdify(x, expr, "numpy")
                Y = f(X)

                label = custom_labels[i] if i < len(custom_labels) and custom_labels[i] else func
                plt.plot(X, Y, linestyle=styles[i % len(styles)], color=colors[i % len(colors)], label=label)

            plt.title(graph_title)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.legend()
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.xlim(x_min, x_max)
            plt.ylim(y_min, y_max)

            # ✅ Apply interval spacing if provided
            if x_interval:
                try:
                    x_interval = float(x_interval)
                    plt.xticks(np.arange(x_min, x_max + x_interval, x_interval))
                except:
                    pass
            if y_interval:
                try:
                    y_interval = float(y_interval)
                    plt.yticks(np.arange(y_min, y_max + y_interval, y_interval))
                except:
                    pass

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plot_url = base64.b64encode(buf.getvalue()).decode("utf-8")
            plt.close()

            last_plot_data = buf.getvalue()

        except Exception:
            error_message = "Invalid function(s) or range. Please try again."

    return render_template("index.html", plot_url=plot_url, error_message=error_message)

@app.route("/download")
def download_plot():
    global last_plot_data
    if last_plot_data:
        buf = io.BytesIO(last_plot_data)
        buf.seek(0)
        return send_file(buf, mimetype="image/png", as_attachment=True, download_name="plot.png")
    else:
        return "No plot available to download. Please generate one first."

if __name__ == "__main__":
    app.run(debug=True)


import gradio as gr

def predict(text):
    return f"Processed: {text}"

demo = gr.Interface(fn=predict, inputs="text", outputs="text")

demo.launch()
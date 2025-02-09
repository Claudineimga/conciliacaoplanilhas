from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
import os
import tempfile

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # Necessário para usar o flash

# Pasta temporária para armazenar os arquivos
UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Página inicial
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        arquivo1 = request.files["arquivo1"]
        arquivo2 = request.files["arquivo2"]

        # Verificar se os arquivos foram enviados
        if arquivo1.filename == "" or arquivo2.filename == "":
            flash("Por favor, selecione ambos os arquivos.", "error")
            return redirect(url_for("index"))

        # Verificar se os arquivos são Excel
        if not (arquivo1.filename.endswith(".xlsx") and arquivo2.filename.endswith(".xlsx")):
            flash("Por favor, envie arquivos no formato .xlsx.", "error")
            return redirect(url_for("index"))

        try:
            # Salvar os arquivos temporariamente
            caminho_arquivo1 = os.path.join(app.config['UPLOAD_FOLDER'], arquivo1.filename)
            caminho_arquivo2 = os.path.join(app.config['UPLOAD_FOLDER'], arquivo2.filename)
            arquivo1.save(caminho_arquivo1)
            arquivo2.save(caminho_arquivo2)

            # Ler os arquivos Excel
            planilha1 = pd.read_excel(caminho_arquivo1)
            planilha2 = pd.read_excel(caminho_arquivo2)

            # Obter as colunas de cada planilha
            colunas_planilha1 = planilha1.columns.tolist()
            colunas_planilha2 = planilha2.columns.tolist()

            # Passar as colunas e caminhos dos arquivos para o template
            return render_template(
                "index.html",
                show_columns=True,
                colunas_planilha1=colunas_planilha1,
                colunas_planilha2=colunas_planilha2,
                arquivo1_name=arquivo1.filename,
                arquivo2_name=arquivo2.filename,
                caminho_arquivo1=caminho_arquivo1,
                caminho_arquivo2=caminho_arquivo2
            )

        except Exception as e:
            flash(f"Ocorreu um erro durante o processamento: {str(e)}", "error")
            return redirect(url_for("index"))

    return render_template("index.html", show_columns=False)

# Rota para processar a conciliação
@app.route("/processar", methods=["POST"])
def processar():
    coluna1 = request.form["coluna1"]
    coluna2 = request.form["coluna2"]
    caminho_arquivo1 = request.form["caminho_arquivo1"]
    caminho_arquivo2 = request.form["caminho_arquivo2"]

    try:
        # Ler os arquivos Excel
        planilha1 = pd.read_excel(caminho_arquivo1)
        planilha2 = pd.read_excel(caminho_arquivo2)

        # Realizar a conciliação
        encontrados = pd.merge(
            planilha1, planilha2, left_on=coluna1, right_on=coluna2, how="inner"
        )
        nao_encontrados_planilha1 = planilha2[~planilha2[coluna2].isin(planilha1[coluna1])]
        nao_encontrados_planilha2 = planilha1[~planilha1[coluna1].isin(planilha2[coluna2])]

        # Salvar os resultados em um arquivo Excel
        caminho_saida = "resultado_final.xlsx"
        with pd.ExcelWriter(caminho_saida) as writer:
            encontrados.to_excel(writer, sheet_name="Encontrados", index=False)
            nao_encontrados_planilha1.to_excel(writer, sheet_name="Nao_Encontrados_Planilha1", index=False)
            nao_encontrados_planilha2.to_excel(writer, sheet_name="Nao_Encontrados_Planilha2", index=False)

        flash("Conciliação concluída com sucesso! Clique no botão abaixo para baixar o arquivo.", "success")
        return render_template("index.html", show_download=True, show_columns=False)

    except Exception as e:
        flash(f"Ocorreu um erro durante o processamento: {str(e)}", "error")
        return redirect(url_for("index"))

# Rota para download do arquivo
@app.route("/download")
def download():
    return send_file("resultado_final.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
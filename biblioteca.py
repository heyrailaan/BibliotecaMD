import tkinter as tk
import tkinter.messagebox as messagebox
import datetime
import sqlite3
import datetime
from tkcalendar import Calendar
from tkinter import ttk
import datetime
import PySimpleGUI as sg
import os
import re
import schedule
import time
from tkinter import Tk, Label
from tkinter import font
from PIL import Image, ImageTk
from tkinter.ttk import Combobox

original_width = 405
original_height = 191
original_x = 0
original_y = 0

livros = {
    "Línguas Estrangeira": [],
    "Filosofia": [],
    "Inglês e Línguas Estrangeira": [],
    "História": [],
    "Infanto Juvenil": [],
    "Português e Grámatica": [],
    "Biologia": [],
    "Matemática": [],
    "Política": [],
    "Física": [],
    "Literatura Romântica ": [],
    "Revistas (com GIBI)": [],
    "Dicionário": [],
    "Poesias, Contos e Crônicas": [],
    "Enciclopédia": [],
    "Informática": [],
    "Psicologia": [],
    "Outros": []
}

categorias = {
    "Línguas Estrangeira": 0,
    "Filosofia": 0,
    "Inglês e Línguas Estrangeira": 0,
    "História": 0,
    "Infanto Juvenil": 0,
    "Português e Gramática": 0,
    "Biologia": 0,
    "Matemática": 0,
    "Política": 0,
    "Física": 0,
    "Literatura Romântica": 0,
    "Revistas (com GIBI)": 0,
    "Dicionário": 0,
    "Poesias, Contos e Crônicas": 0,
    "Enciclopédia": 0,
    "Informática": 0,
    "Psicologia": 0,
    "Outros": 0
}

# Lista de alunos que pegaram livros
alunos_com_livros = []
alunos_devolver_livros = []

# Variáveis globais para as tabelas
livros_treeview = None
alunos_treeview = None

def criar_tabela():
    conn = sqlite3.connect("login.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT, senha TEXT)")
    conn.commit()
    conn.close()

def criar_tabelas_biblioteca():
    # Conecta-se ao banco de dados da biblioteca
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()

    # Cria a tabela de categorias se ela não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categorias (
        categoria TEXT PRIMARY KEY,
        totais INTEGER DEFAULT 0
    )
    ''')

    # Adiciona as categorias ao banco de dados se elas não existirem
    for categoria in categorias:
        cursor.execute("INSERT OR IGNORE INTO categorias (categoria) VALUES (?)", (categoria,))

    # Modifique a tabela de alunos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY,
        nome TEXT CHECK (nome GLOB '[A-Z]*'),
        turma TEXT CHECK (turma = UPPER(turma))
    )
    ''')

    # Crie a tabela de empréstimos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS emprestimos (
        id INTEGER PRIMARY KEY,
        id_aluno INTEGER,
        livro TEXT,
        data_entrega TEXT,
        data_devolucao TEXT,
        status TEXT DEFAULT 'Pendente',
        FOREIGN KEY (id_aluno) REFERENCES alunos (id)
    )
    ''')
    # Commit as alterações e feche a conexão
    conn.commit()
    conn.close()

def carregar_livros():
    global livros
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categorias")
    rows = cursor.fetchall()
    livros = {
        "Línguas Estrangeira": [],
        "Filosofia": [],
        "Inglês e Línguas Estrangeira": [],
        "História": [],
        "Infanto Juvenil": [],
        "Português e Grámatica": [],
        "Biologia": [],
        "Matemática": [],
        "Política": [],
        "Física": [],
        "Literatura Romântica": [],
        "Revistas (com GIBI)": [],
        "Dicionário": [],
        "Poesias, Contos e Crônicas": [],
        "Enciclopédia": [],
        "Informática": [],
        "Psicologia": [],
        "Outros": []
    }
    for row in rows:
        if len(row) >= 5 and all(row[1:5]):  # Verifica se todos os campos necessários estão preenchidos
            livro = {
                "titulo": row[1],
                "categoria": row[2],
                "numero": row[4]
            }
            livros[row[2]].append(livro)  # Use a categoria do banco de dados
    conn.close()
    
def carregar_alunos():
    global alunos_com_livros
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()

    # Consulta para obter informações dos alunos e seus empréstimos
    cursor.execute('''
    SELECT alunos.id, alunos.nome, alunos.turma, emprestimos.livro, emprestimos.data_entrega, emprestimos.data_devolucao, emprestimos.status
    FROM alunos
    LEFT JOIN emprestimos ON alunos.id = emprestimos.id_aluno
    ''')

    rows = cursor.fetchall()

    alunos_com_livros = []

    for row in rows:
        aluno_id, nome, turma, livro, data_entrega, data_devolucao, status = row

        # Crie uma estrutura de dados para representar o aluno com seus empréstimos
        aluno = {
            "id": aluno_id,
            "nome": nome,
            "turma": turma,
            "livro": livro,
            "data_entrega": data_entrega,
            "data_devolucao": data_devolucao,
            "status": status
        }

        # Verifique se o aluno tem um livro emprestado
        if aluno["livro"]:
            alunos_com_livros.append(aluno)

    conn.close()

def adicionar_aluno(nome, turma, livro, data_entrega, data_devolucao, status, window):
    if not nome or not turma or not livro or not data_entrega or not data_devolucao:
        print("Preencha todos os campos obrigatórios!")
        return

    # Conecta ao banco de dados
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()

    # Verifica se o aluno já existe no banco de dados
    cursor.execute("SELECT id FROM alunos WHERE nome = ? AND turma = ?", (nome, turma))
    aluno_id = cursor.fetchone()

    if aluno_id is None:
        # O aluno não existe, então é inserido o aluno na tabela de alunos
        cursor.execute("INSERT INTO alunos (nome, turma) VALUES (?, ?)", (nome, turma))
        aluno_id = cursor.lastrowid  # Obtém o ID do aluno recém-inserido
    else:
        aluno_id = aluno_id[0]  # Obtém o primeiro valor da tupla (o ID do aluno)

    # Insirido um novo registro na tabela de empréstimos
    cursor.execute("INSERT INTO emprestimos (id_aluno, livro, data_entrega, data_devolucao, status) VALUES (?, ?, ?, ?, ?)",
        (aluno_id, livro, data_entrega, data_devolucao, status))

    # Commit as alterações e fechamento da conexão com o banco de dados
    conn.commit()
    conn.close()

    window.destroy()
    carregar_tabela_alunos()

def remover_aluno_selecionado():
    # Verificar se um aluno foi selecionado na tabela
    item = alunos_treeview.selection()
    if not item:
        messagebox.showinfo("Erro", "Por favor, selecione um aluno para remover.")
        return

    # Obter as informações do aluno selecionado
    aluno_values = alunos_treeview.item(item, 'values')
    if aluno_values:
        # Extrair nome e turma do aluno selecionado
        aluno_nomeesobrenome = aluno_values[0]
        aluno_turma = aluno_values[1]

        # Remover o aluno do banco de dados
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alunos WHERE nome=? AND turma=?", (aluno_nomeesobrenome, aluno_turma))
        conn.commit()
        conn.close()

        # Remover o aluno da tabela de alunos
        alunos_treeview.delete(item)
        messagebox.showinfo("Sucesso", f"{aluno_nomeesobrenome} da turma {aluno_turma} foi removido da tabela de alunos.")
        atualizar_banco_de_dados()

def verificar_login():
    # Obter as credenciais do usuário e senha inseridas
    usuario = usuario_entry.get()
    senha = senha_entry.get()

    # Verificar as credenciais de login
    if usuario == "biblioteca" and senha == "123":
        login_frame.pack_forget()
        abrir_pagina_principal(usuario)

        # Salvar as credenciais se a opção 'Lembrar-me' estiver marcada
        if lembrar_me_var.get() == 1:
            os.makedirs(os.path.expandvars('%LOCALAPPDATA%\\BibliotecaMD'), exist_ok=True)
            with open(os.path.expandvars('%LOCALAPPDATA%\\BibliotecaMD\\credenciais.tmp'), 'w') as f:
                f.write(f'{usuario}\n{senha}')
    else:
        erro_label.config(text="Credenciais inválidas")

def carregar_detalhes_aluno(aluno_nome, aluno_turma, treeview):
    # Conectar ao banco de dados e consultar os detalhes do aluno
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT livros_emprestados FROM alunos WHERE nome = ? AND turma = ?", (aluno_nome, aluno_turma))
    result = cursor.fetchone()

    if result is not None:
        livros_emprestados = result[0]
        treeview.insert("", "end", values=(livros_emprestados))

    # Fechar a conexão com o banco de dados
    conn.close()

def atualizar_data_devolucao():
    nova_data = entry_nova_data.get()
    if nova_data:
        try:
            # Conectar ao banco de dados
            conn = sqlite3.connect("biblioteca.db")
            cursor = conn.cursor()
            
            # Atualizar a coluna 'data_devolucao' na tabela 'alunos' para o livro selecionado
            cursor.execute("UPDATE alunos SET data_devolucao = ? WHERE nome = ? AND livro = ?", (nova_data, aluno_nome, livro_selecionado))
            conn.commit()
            conn.close()
            
            janela_data_devolucao.destroy()
            messagebox.showwarning("Aviso", f"Data de devolução para {nova_data} atualizada com sucesso.")
            
            # Recarregar os livros e datas após a atualização
            carregar_livros_emprestados(aluno_nome, aluno_turma, livros_emprestados_treeview)
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar a data de devolução: {str(e)}")
    else:
        messagebox.showwarning("Aviso", "Por favor, insira uma nova data de devolução.")

def carregar_tabela_livros():
    if livros_treeview:
        livros_treeview.delete(*livros_treeview.get_children())
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()

        # Consultar as categorias e totais diretamente do banco de dados
        cursor.execute("SELECT categoria, totais FROM categorias")
        rows = cursor.fetchall()

        for row in rows:
            categoria, totais = row[0], row[1]
            livros_treeview.insert("", "end", values=(categoria, totais))

        conn.close()

# Função para carregar a tabela de alunos
def carregar_tabela_alunos():
    if alunos_treeview:
        alunos_treeview.delete(*alunos_treeview.get_children())
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()

        # Consulta para obter alunos distintos com empréstimos ativos e seus status
        cursor.execute('''
        SELECT DISTINCT alunos.nome, alunos.turma, emprestimos.status
        FROM alunos
        JOIN emprestimos ON alunos.id = emprestimos.id_aluno
        ''')

        rows = cursor.fetchall()

        for row in rows:
            nome, turma, status = row

            # Inserir o nome do aluno, a turma e o status
            alunos_treeview.insert("", "end", values=(nome, turma, status))

        conn.close()

def adicionar_aluno_gui():
    adicionar_aluno_window = tk.Toplevel(root)
    adicionar_aluno_window.title("Biblioteca - Adicionar aluno(a)")

    nome_label = tk.Label(adicionar_aluno_window, text="Nome do Aluno:")
    nome_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    nome_entry = tk.Entry(adicionar_aluno_window)
    nome_entry.grid(row=0, column=1, padx=10, pady=10)

    turma_label = tk.Label(adicionar_aluno_window, text="Turma:")
    turma_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
    turma_entry = tk.Entry(adicionar_aluno_window)
    turma_entry.grid(row=1, column=1, padx=10, pady=10)

    livro_label = tk.Label(adicionar_aluno_window, text="Nome do Livro:")
    livro_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
    livro_entry = tk.Entry(adicionar_aluno_window)
    livro_entry.grid(row=2, column=1, padx=10, pady=10)

    data_entrega_label = tk.Label(adicionar_aluno_window, text="Data de Entrega:")
    data_entrega_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

    data_entrega_cal = Calendar(adicionar_aluno_window, selectmode="day")
    data_entrega_cal.grid(row=3, column=1, padx=10, pady=10)
    
    data_devolucao_label = tk.Label(adicionar_aluno_window, text="Data de Devolução:")
    data_devolucao_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
    
    data_devolucao_cal = Calendar(adicionar_aluno_window, selectmode="day")
    data_devolucao_cal.grid(row=4, column=1, padx=10, pady=10)

    status_label = tk.Label(adicionar_aluno_window, text="Status do Livro:")
    status_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")

    status_combobox = Combobox(adicionar_aluno_window, values=["Disponível", "Emprestado", "Atrasado", "Perdido ou Danificado", "Reservado"])
    status_combobox.grid(row=6, column=0, columnspan=2, padx=10, pady=10)


    adicionar_button = tk.Button(adicionar_aluno_window, text="Adicionar Aluno", command=lambda: adicionar_aluno(
    nome_entry.get(), turma_entry.get(), livro_entry.get(), data_entrega_cal.get_date(), data_devolucao_cal.get_date(), status_combobox.get(), adicionar_aluno_window))
    adicionar_button.grid(row=7, column=0, columnspan=2, pady=10)
        
def confirmar_logout():
    resultado = messagebox.askquestion("Sair", "Deseja realmente sair?")

    if resultado == "yes":
        logout()
    else:
        pass

def logout():
    global principal_frame

    root.geometry(f"{original_width}x{original_height}")
    principal_frame.pack_forget()
    login_frame.pack()

def adicionar_livro(nome, categoria, autor, numero, adicionar_livro_window):
    # Verificar se todos os campos estão preenchidos
    if not nome or not categoria or not autor or not numero:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    # Adicionar o livro à lista apropriada
    livro = {
        "titulo": nome,
        "autor": autor,
        "categoria": categoria,
        "numero": numero
    }
    livros[categoria].append(livro)

    # Adicionar o livro ao banco de dados
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    # Inserir o livro na tabela de livros
    cursor.execute("INSERT INTO livros (titulo, autor, categoria, numero) VALUES (?, ?, ?, ?)",
                   (titulo, autor, categoria, numero))

    # Atualizar o total de livros na categoria
    cursor.execute("UPDATE categorias SET totais = totais + 1 WHERE categoria = ?", (categoria,))
    conn.commit()
    conn.close()

    # Fechar a janela de adição de livro
    adicionar_livro_window.destroy()

    # Recarregar a tabela de livros
    carregar_tabela_livros()

def remover_livro():
    livro_selecionado = livros_treeview.selection()
    if not livro_selecionado:
        messagebox.showerror("Erro", "Por favor, selecione um livro para remover.")
        return

    item = livros_treeview.item(livro_selecionado)
    livro_info = item["values"]

    # Encontrar o livro na lista de acordo com as informações exibidas
    for categoria, lista_livros in livros.items():
        for livro in lista_livros:
            if livro["titulo"] == livro_info[0] and livro["categoria"] == livro_info[1] and livro["autor"] == livro_info[2] and livro["numero"] == livro_info[3]:
                lista_livros.remove(livro)

                # Remover o livro do banco de dados
                conn = sqlite3.connect("biblioteca.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM livros WHERE titulo=? AND categoria=? AND autor=? AND numero=?",
                               (livro_info[0], livro_info[1], livro_info[2], livro_info[3]))
                conn.commit()
                conn.close()

                # Recarregar a tabela de livros
                carregar_tabela_livros()
                return

def is_data_brasileira(data):
    # Verificar se a data está no formato brasileiro (dd/mm/aaaa)
    partes = data.split('/')
    if len(partes) == 3:
        dia, mes, ano = partes
        if len(dia) == 2 and len(mes) == 2 and len(ano) == 4:
            return True
    return False

def converter_data(data):
    if is_data_brasileira(data):
        # A data está no formato brasileiro, então vou convertê-la para o formato americano (english)
        partes = data.split('/')
        data_americana = f"{partes[1]}/{partes[0]}/{partes[2]}"
        return data_americana
    else:
        # A data está no formato americano, então vou convertê-la para o formato brasileiro
        partes = data.split('/')
        data_brasileira = f"{partes[1]}/{partes[0]}/{partes[2]}"
        return data_brasileira

def carregar_livros_emprestados(aluno_nome, aluno_turma, treeview):
    # Limpar a Treeview antes de carregar os livros emprestados
    for item in treeview.get_children():
        treeview.delete(item)

    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect("biblioteca.db")
        cursor = conn.cursor()

        # Obter o ID do aluno com base no nome e turma
        cursor.execute("SELECT id FROM alunos WHERE nome = ? AND turma = ?", (aluno_nome, aluno_turma))
        aluno_id = cursor.fetchone()

        if aluno_id:
            aluno_id = aluno_id[0]

            # Executar uma consulta para obter os livros emprestados pelo aluno
            cursor.execute("SELECT livro, data_entrega, data_devolucao, status FROM empréstimos WHERE id_aluno = ?", (aluno_id,))
            results = cursor.fetchall()

            for result in results:
                livro, data_entrega, data_devolucao, status = result
                # Verificar se a data está no formato brasileiro e converter para o formato americano
                if is_data_brasileira(data_entrega):
                    data_entrega = converter_data(data_entrega)

                if is_data_brasileira(data_devolucao):
                    data_devolucao = converter_data(data_devolucao)

                treeview.insert("", "end", values=(livro, f"{data_entrega} - {data_devolução}", status))

        # Fechar a conexão com o banco de dados
        conn.close()

    except sqlite3.Error as e:
        print(f"Erro ao carregar livros emprestados: {str(e)}")

janela_alterar_data = None
livros_emprestados_treeview = None
tabela_totais = None
janela_detalhes_aberta = None

def abrir_gui_preencher_campo(aluno_id, aluno_nome, aluno_turma):
    item = alunos_treeview.selection()
    if not item:
        return
    selected_book = livros_emprestados_treeview.selection()
    if selected_book:
        livro_selecionado = livros_emprestados_treeview.item(selected_book, 'values')[0]
        if livro_selecionado:
        
            aluno_info = alunos_treeview.item(item, 'values')
            aluno_nome = aluno_info[0]
            aluno_turma = aluno_info[1]
        
            # Cria uma janela para o usuário inserir a nova data de devolução
            janela_data_devolucao = tk.Toplevel(root)
            janela_data_devolucao.title(f"Nova data devolução: {livro_selecionado}")
            
            # Definir o tamanho da janela
            janela_data_devolucao.geometry("577x178")

            # Proíbe o redimensionamento da janela
            janela_data_devolucao.resizable(False, False)

            # Centraliza a janela
            window_width = 577
            window_height = 178
            screen_width = janela_data_devolucao.winfo_screenwidth()
            screen_height = janela_data_devolucao.winfo_screenheight()
            x_coordinate = (screen_width / 2) - (window_width / 2)
            y_coordinate = (screen_height / 2) - (window_height / 2)
            janela_data_devolucao.geometry("+%d+%d" % (x_coordinate, y_coordinate))

            # Crie uma Entry para inserir a nova data de devolução
            entry_nova_data = tk.Entry(janela_data_devolucao)
            entry_nova_data.pack()

            # Função para atualizar a data de devolução
            def atualizar_data_devolucao():
                nova_data = entry_nova_data.get()
                if nova_data:
                    try:
                        # Conecta ao banco de dados
                        conn = sqlite3.connect("biblioteca.db")
                        cursor = conn.cursor()

                        nova_data = datetime.datetime.strptime(nova_data, "%d/%m/%y").date()
                        nova_data_formatada = nova_data.strftime('%m/%d/%y')
                        
                        # Atualize a coluna 'data_devolucao' na tabela 'emprestimos' para o livro selecionado
                        cursor.execute("UPDATE emprestimos SET data_devolucao = ? WHERE id_aluno = ? AND livro = ?", (nova_data_formatada, aluno_id, livro_selecionado))
                        


                        conn.commit()
                        conn.close()
                        janela_data_devolucao.destroy()
                        messagebox.showinfo("Sucesso", f"Data de devolução para {livro_selecionado} atualizada com sucesso.")
                        # Recarregue os livros e datas após a atualização
                        carregar_livros_emprestados(aluno_nome, aluno_turma, livros_emprestados_treeview)
                    except sqlite3.Error as e:
                        messagebox.showerror("Erro", f"Erro ao atualizar a data de devolução: {str(e)}")
                else:
                    messagebox.showwarning("Aviso", "Por favor, insira uma nova data de devolução.")
            
            # Crie um Frame para centralizar o botão
            frame = tk.Frame(janela_data_devolucao)
            frame.pack()

            # Crie um botão para confirmar a atualização da data de devolução
            btn_atualizar_data_devolucao = tk.Button(frame, text="Atualizar Data de Devolução", command=atualizar_data_devolucao)
            btn_atualizar_data_devolucao.pack()

def abrir_gui_detalhes_aluno():
    item = alunos_treeview.selection()
    if not item:
        return

    # Obtenha as informações do aluno selecionado
    aluno_info = alunos_treeview.item(item, 'values')
    aluno_nome = aluno_info[0]
    aluno_turma = aluno_info[1]

    # Obtenha o ID do aluno
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM alunos WHERE nome = ? AND turma = ?", (aluno_nome, aluno_turma))
    aluno_id = cursor.fetchone()[0]
    conn.close()
    
    global janela_alterar_data, livros_emprestados_treeview, btn_atualizar_data_devolucao, btn_atualizar_status_livro
    if janela_alterar_data is None or not janela_alterar_data.winfo_exists():
        janela_alterar_data = tk.Toplevel(root)
        janela_alterar_data.title(f"Biblioteca - {aluno_nome} {aluno_turma}")


        # Defina livros_emprestados_treeview aqui
        livros_emprestados_treeview = ttk.Treeview(janela_alterar_data, columns=("Livro", "Data de Entrega - Data de Devolução", "Status"))
        livros_emprestados_treeview.heading("#1", text="Livro")
        livros_emprestados_treeview.heading("#2", text="Data de Entrega - Data de Devolução")
        livros_emprestados_treeview.heading("#3", text="Status")
        livros_emprestados_treeview.column("#1", width=200)
        livros_emprestados_treeview.column("#2", width=200)
        livros_emprestados_treeview.column("#3", width=100)
        livros_emprestados_treeview.pack()
        livros_emprestados_treeview['show'] = 'headings'

        # Agora, carregue os livros, datas e status na Treeview
        carregar_livros_emprestados(aluno_nome, aluno_turma, livros_emprestados_treeview)

        # Adicione um evento de clique à Treeview
        def on_book_select(event):
            global livro_selecionado
            selected_book = livros_emprestados_treeview.selection()
            if selected_book:
                livro_selecionado = livros_emprestados_treeview.item(selected_book, 'values')[0]

        livros_emprestados_treeview.bind('<<TreeviewSelect>>', on_book_select)

        # Adicione um botão para abrir a interface de atualização da data de devolução
        btn_atualizar_data_devolucao = tk.Button(janela_alterar_data, text="Atualizar Devolução", command=lambda: abrir_gui_preencher_campo(aluno_id, aluno_nome, aluno_turma))
        btn_atualizar_data_devolucao.pack()

        # Adicione um botão para atualizar o status do livro
        btn_atualizar_status_livro = tk.Button(janela_alterar_data, text="Atualizar Status do Livro", command=lambda: abrir_gui_atualizar_status_livro(aluno_id, aluno_nome, aluno_turma, livro_selecionado))
        btn_atualizar_status_livro.pack()

    else:
        # Se a janela já existir, limpe a Treeview antes de carregar os novos dados
        for item in livros_emprestados_treeview.get_children():
            livros_emprestados_treeview.delete(item)
        janela_alterar_data.lift()
        
# Adicione a função para abrir a interface de atualização do status do livro
def abrir_gui_atualizar_status_livro(aluno_id, aluno_nome, aluno_turma, livro):
    # Crie uma janela para o usuário atualizar o status do livro
    janela_atualizar_status_livro = tk.Toplevel(root)
    janela_atualizar_status_livro.title(f"Atualizar Status do Livro: {livro}")

    # Defina o tamanho da janela
    janela_atualizar_status_livro.geometry("400x200")

    # Proíbe o redimensionamento da janela
    janela_atualizar_status_livro.resizable(False, False)

    # Centralize a janela
    window_width = 400
    window_height = 200
    screen_width = janela_atualizar_status_livro.winfo_screenwidth()
    screen_height = janela_atualizar_status_livro.winfo_screenheight()
    x_coordinate = (screen_width / 2) - (window_width / 2)
    y_coordinate = (screen_height / 2) - (window_height / 2)
    janela_atualizar_status_livro.geometry("+%d+%d" % (x_coordinate, y_coordinate))

    # Crie uma Entry para inserir o novo status
    entry_novo_status = tk.Entry(janela_atualizar_status_livro)
    entry_novo_status.pack()

    # Função para atualizar o status do livro
    def atualizar_status_livro():
        novo_status = entry_novo_status.get()
        if novo_status:
            try:
                # Conecte-se ao banco de dados
                conn = sqlite3.connect("biblioteca.db")
                cursor = conn.cursor()
                # Atualize o status do livro na tabela 'emprestimos' para o livro selecionado
                cursor.execute("UPDATE emprestimos SET status = ? WHERE id_aluno = ? AND livro = ?", (novo_status, aluno_id, livro))
                conn.commit()
                conn.close()
                janela_atualizar_status_livro.destroy()
                messagebox.showinfo("Sucesso", f"Status do livro {livro} atualizado com sucesso.")
                # Recarregue os livros, datas e status após a atualização
                carregar_livros_emprestados(aluno_nome, aluno_turma, livros_emprestados_treeview)
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Erro ao atualizar o status do livro: {str(e)}")
        else:
            messagebox.showwarning("Aviso", "Por favor, insira o novo status do livro.")
    
    # Crie um Frame para centralizar o botão
    frame = tk.Frame(janela_atualizar_status_livro)
    frame.pack()

    # Crie um botão para confirmar a atualização do status do livro
    btn_atualizar_status = tk.Button(frame, text="Atualizar Status do Livro", command=atualizar_status_livro)
    btn_atualizar_status.pack()

def atualizar_banco_de_dados():
    # Conecta-se ao banco de dados ou cria-o se não existir
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()

    carregar_livros()
    carregar_alunos()
    carregar_tabela_alunos()
    criar_tabela()
    criar_tabelas_biblioteca()

    conn.close()

def pesquisar_alunos_no_banco_de_dados(termo):
    # Conecte-se ao banco de dados
    conn = sqlite3.connect("biblioteca.db")
    cursor = conn.cursor()

    if not termo:  # Verifique se o termo está vazio
        # Se o termo estiver vazio, não faz a pesquisa completa
        conn.close()
        return

    # Execute a consulta SQL para buscar alunos distintos com base no nome
    cursor.execute('''
        SELECT DISTINCT a.nome, a.turma, e.status
        FROM alunos a
        LEFT JOIN emprestimos e ON a.id = e.id_aluno
        WHERE a.nome LIKE ?
    ''', ('%' + termo + '%',))
    
    resultados = cursor.fetchall()

    # Limpe a Treeview antes de adicionar os resultados da pesquisa
    for item in alunos_treeview.get_children():
        alunos_treeview.delete(item)

    # Adicione os resultados da pesquisa à Treeview
    for resultado in resultados:
        nome_aluno, turma, status = resultado

        # Adicione os resultados à Treeview
        alunos_treeview.insert("", "end", values=(nome_aluno, turma, status))

    # Atualize a Treeview
    alunos_treeview.update()

    # Feche a conexão com o banco de dados
    conn.close()

def abrir_pagina_principal(usuario):
    global principal_frame, livros_treeview, alunos_treeview, atualizar_aluno_button
    
    principal_frame = tk.Frame(root)
    principal_frame.pack()

    root.geometry("1280x720")
    root.title("Biblioteca - Painel de Controle")

    font_roboto = font.nametofont("TkDefaultFont")
    font_roboto.configure(size=11, weight="bold", family="Roboto")
    
    # Carregue a imagem usando o módulo PIL
    imagem = Image.open("manoeldevoto.png")
    imagem = imagem.resize((256, 200), Image.LANCZOS)
    foto = ImageTk.PhotoImage(imagem)

    # Adicione a imagem ao seu aplicativo Tkinter com preenchimento à direita
    label_imagem = tk.Label(principal_frame, image=foto)
    label_imagem.image = foto  # Mantenha uma referência da imagem
    label_imagem.pack(side=tk.LEFT, padx=50)  # Ajuste o valor de padx conforme necessário


    # Use a fonte personalizada para o rótulo
    nome_usuario_label = Label(root, text=f"Bem-vindo, Administrador!", font=font_roboto)
    nome_usuario_label.pack()

    biblioteca_frame = tk.Frame(principal_frame)
    biblioteca_frame.pack(side=tk.LEFT)

    carregar_livros()
    carregar_alunos()

    livros_label = tk.Label(biblioteca_frame, text="Livros:")
    livros_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(10, 0))

    livros_treeview = ttk.Treeview(biblioteca_frame, columns=("Categoria", "Totais"))
    livros_treeview.heading("#1", text="Categoria")
    livros_treeview.heading("#2", text="Totais")
    livros_treeview.column("#1", width=300)
    livros_treeview.column("#2", width=100)
    livros_treeview.pack(side=tk.TOP, anchor="w", padx=10, fill="both")  # Use fill="both" para centralizar verticalmente
    livros_treeview['show'] = 'headings'  # Isso elimina a primeira coluna vazia
    
    for categoria, lista_livros in livros.items():
        for livro in lista_livros:
            livros_treeview.insert("", "end", values=(categoria, livro["numero"]))
        
    livros_treeview.bind("<Double-1>", on_double_click)
     

    alunos_label = tk.Label(biblioteca_frame, text="Banco de Dados:")
    alunos_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(10, 0))

    alunos_treeview = ttk.Treeview(biblioteca_frame, columns=("ESTUDANTE", "TURMA", "ESTADO"))
    alunos_treeview.heading("#1", text="ESTUDANTE")
    alunos_treeview.heading("#2", text="TURMA")
    alunos_treeview.heading("#3", text="ESTADO")
    alunos_treeview.column("#1", width=200)
    alunos_treeview.column("#2", width=100)
    alunos_treeview.column("#3", width=600)
    alunos_treeview.pack(side=tk.TOP, anchor="w", padx=10, fill="both")  # Use fill="both" para centralizar verticalmente
    alunos_treeview['show'] = 'headings'  # Isso elimina a primeira coluna vazia
    
    carregar_tabela_livros()
    carregar_tabela_alunos()

    botoes_frame = tk.Frame(biblioteca_frame)
    botoes_frame.pack(side=tk.LEFT)

    atualizar_aluno_button = tk.Button(botoes_frame, text="Ver livro", command=abrir_gui_detalhes_aluno)
    atualizar_aluno_button.pack(side=tk.LEFT)

    # Cria o pesquisar_frame após o botão "Ver livro"
    pesquisar_frame = tk.Frame(biblioteca_frame)
    pesquisar_frame.pack(side=tk.LEFT)

    # Assim, adicionar o rótulo e a barra de pesquisa dentro do pesquisar_frame
    pesquisar_label = tk.Label(pesquisar_frame, text="Pesquisar Aluno(A):")
    pesquisar_label.grid(row=0, column=0, sticky="w")

    # Adiciona a Entry (barra de pesquisa) para buscar alunos
    search_entry = tk.Entry(pesquisar_frame)
    search_entry.grid(row=0, column=1, sticky="w")
    search_entry.bind("<KeyRelease>", lambda event: pesquisar_alunos_no_banco_de_dados(search_entry.get()))

    adicionar_aluno_button = tk.Button(botoes_frame, text="Adicionar Aluno", command=adicionar_aluno_gui)
    adicionar_aluno_button.pack(side=tk.LEFT, padx=10, pady=5)

    remover_aluno_button = ttk.Button(botoes_frame, text="Remover Aluno", command=remover_aluno_selecionado)
    remover_aluno_button.pack(side=tk.LEFT, padx=10, pady=5)

    logout_button = tk.Button(botoes_frame, text="Logout", command=confirmar_logout)
    logout_button.pack(side=tk.LEFT, padx=10, pady=5)

    atualizar_banco_de_dados()



def on_double_click(event):
    item = livros_treeview.selection()[0]  # Obtenha o item selecionado
    categoria = livros_treeview.item(item, 'values')[0]
    quantidade_atual = livros_treeview.item(item, 'values')[1]

    # Cria uma janela para que o usuário insira a nova quantidade
    janela_quantidade = tk.Toplevel(root)
    janela_quantidade.title(f"Biblioteca - {categoria}")

    # Cria uma Entry para inserir a nova quantidade
    entry_nova_quantidade = tk.Entry(janela_quantidade)
    entry_nova_quantidade.pack()

    # Preenche o Entry com a quantidade atual
    entry_nova_quantidade.insert(0, quantidade_atual)

    # Função para atualizar a quantidade
    def atualizar_quantidade():
        nova_quantidade = entry_nova_quantidade.get()
        if nova_quantidade:
            try:
                # Conecte-se ao banco de dados
                conn = sqlite3.connect("biblioteca.db")
                cursor = conn.cursor()
                # Atualiza a coluna 'quantidade' na tabela 'categoria' para a categoria selecionada
                cursor.execute("UPDATE categorias SET totais = ? WHERE categoria = ?", (nova_quantidade, categoria))
                conn.commit()
                conn.close()
                janela_quantidade.destroy()
                messagebox.showinfo("Sucesso", f"Quantidade para {categoria} atualizada com sucesso.")
                # Recarregue as categorias e quantidades após a atualização
                carregar_livros()
                carregar_tabela_livros()
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Erro ao atualizar a quantidade: {str(e)}")
        else:
            messagebox.showwarning("Aviso", "Por favor, insira uma nova quantidade.")

    # Cria um botão para confirmar a atualização da quantidade
    btn_atualizar_quantidade = tk.Button(janela_quantidade, text="Atualizar Quantidade", command=atualizar_quantidade)
    btn_atualizar_quantidade.pack()

root = tk.Tk()
root.geometry(f"{original_width}x{original_height}")
root.title("Biblioteca - Administração")
root.resizable(False, False)

login_frame = tk.Frame(root)
login_frame.pack()

usuario_label = tk.Label(login_frame, text="Usuário:")
usuario_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
usuario_entry = tk.Entry(login_frame)
usuario_entry.grid(row=0, column=1, padx=10, pady=10)

senha_label = tk.Label(login_frame, text="Senha:")
senha_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
senha_entry = tk.Entry(login_frame, show="*")
senha_entry.grid(row=1, column=1, padx=10, pady=10)

lembrar_me_var = tk.IntVar()
lembrar_me_checkbutton = tk.Checkbutton(login_frame, text="Lembrar-me", variable=lembrar_me_var)
lembrar_me_checkbutton.grid(row=2, column=1, sticky="w")

if os.path.exists(os.path.expandvars('%LOCALAPPDATA%\\BibliotecaMD\\credenciais.tmp')):
    with open(os.path.expandvars('%LOCALAPPDATA%\\BibliotecaMD\\credenciais.tmp'), 'r') as f:
        saved_credentials = f.read().splitlines()
        if len(saved_credentials) == 2:
            usuario_entry.insert(0, saved_credentials[0])
            senha_entry.insert(0, saved_credentials[1])
            lembrar_me_var.set(1)
        verificar_login()

login_button = tk.Button(login_frame, text="Login", command=verificar_login)
login_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

erro_label = tk.Label(login_frame, text="", fg="red")
erro_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

icone = Image.open("bibli.ico")
root.iconphoto(True, ImageTk.PhotoImage(icone))
criar_tabela()
criar_tabelas_biblioteca()
carregar_livros()
carregar_alunos()
s = ttk.Style()
root.mainloop()

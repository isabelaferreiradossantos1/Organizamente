# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_dopaminergica' # Requerido para gerenciar sessões de login

DB_FILE = 'organizamente.db'

# --- FUNÇÕES DE BANCO DE DADOS ---

def obter_conexao():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            anotacoes_midia TEXT DEFAULT '',
            meta_livros INTEGER DEFAULT 10,
            meta_filmes INTEGER DEFAULT 20,
            copos_agua INTEGER DEFAULT 0,
            exercicio_feito INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de Tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            coluna TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de Metas SMART
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas_smart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            step1_desc TEXT,
            step1_time TEXT,
            step1_deadline TEXT,
            obstacles TEXT,
            plan_obstacles TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de Leituras & Filmes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mídias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            autor TEXT,
            nota INTEGER,
            tipo TEXT NOT NULL,
            concluido INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela Financeira
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    # Tabela de Saldo Inicial por Mês
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldos_iniciais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            valor REAL DEFAULT 0.0,
            UNIQUE(user_id, ano, mes),
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela Quero vs Preciso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desejos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor_previsto REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    # NOVA TABELA: Saúde Checkup (Terapia, Exames, Medicamentos, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saude_checkup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            titulo TEXT NOT NULL, -- 'Terapia', 'Exame de Sangue', ou Nome do Remédio
            categoria TEXT NOT NULL, -- 'terapia', 'exames', 'medicamento'
            data TEXT, -- YYYY-MM-DD
            hora TEXT, -- HH:MM
            status TEXT DEFAULT 'agendado', -- 'agendado' ou 'concluido'
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

inicializar_banco()

# --- HELPER FUNCTIONS ---

def obter_sobra_mes(conn, user_id, ano, mes):
    saldo_man = conn.execute(
        'SELECT valor FROM saldos_iniciais WHERE user_id = ? AND ano = ? AND mes = ?', 
        (user_id, ano, mes)
    ).fetchone()

    if saldo_man:
        saldo_inicial = saldo_man['valor']
    else:
        if mes == 1:
            prev_mes, prev_ano = 12, ano - 1
        else:
            prev_mes, prev_ano = mes - 1, ano

        hoje = datetime.now()
        if (ano < hoje.year - 2):
            saldo_inicial = 0.0
        else:
            saldo_inicial = obter_sobra_mes(conn, user_id, prev_ano, prev_mes)

    transacoes = conn.execute(
        'SELECT valor, tipo FROM financeiro WHERE user_id = ? AND ano = ? AND mes = ?',
        (user_id, ano, mes)
    ).fetchall()

    entradas = sum(t['valor'] for t in transacoes if t['tipo'] == 'entradas')
    fixos = sum(t['valor'] for t in transacoes if t['tipo'] == 'gastos_fixos')
    variaveis = sum(t['valor'] for t in transacoes if t['tipo'] == 'gastos_variaveis')

    return saldo_inicial + entries - (fixos + variaveis) if 'entries' in locals() else saldo_inicial + entradas - (fixos + variaveis)

# --- TEMPLATE HTML COMPLETO ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#D46A43">
    <title>OrganizaMente</title>
    <style>
        :root {
            --bg-color: #FAF6F0; /* Bege Acolhedor */
            --card-bg: #FFFFFF;
            --text-main: #3D261C; /* Chocolate Brown */
            --text-muted: #7A695E;
            --accent-terracotta: #D46A43; /* Terracota */
            --accent-peach: #F3B391; /* Pêssego Suave */
            --accent-green: #81B29A; /* Verde Sálvia */
            --accent-red: #E07A5F; 
            --border-color: #EADEC9;
            --star-color: #F4C430;
            --accent-blue: #A8DADC; /* Azul suave para a aba saúde */
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        header {
            text-align: center;
            margin-top: 15px;
            margin-bottom: 25px;
            width: 100%;
            max-width: 600px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-size: 1.5rem;
            margin: 0;
            color: var(--accent-terracotta);
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        h1 span {
            color: var(--accent-peach);
        }

        .user-badge {
            font-size: 0.8rem;
            background-color: var(--accent-peach);
            color: var(--text-main);
            padding: 6px 14px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: bold;
            transition: opacity 0.2s;
        }

        .user-badge:hover {
            opacity: 0.9;
        }

        /* Telas de Login e Cadastro */
        .auth-container {
            background-color: var(--card-bg);
            padding: 35px 30px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 10px 25px rgba(61, 38, 28, 0.05);
            width: 100%;
            max-width: 360px;
            margin-top: 60px;
            text-align: center;
        }

        .auth-title {
            color: var(--accent-terracotta);
            margin-bottom: 10px;
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        .auth-title span {
            color: var(--accent-peach);
        }

        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 25px;
        }

        .auth-input {
            padding: 14px;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            outline: none;
            font-size: 1rem;
            background-color: #FCFAF7;
            transition: border-color 0.2s;
        }

        .auth-input:focus {
            border-color: var(--accent-terracotta);
        }

        .auth-btn {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
            transition: transform 0.1s, background-color 0.2s;
        }

        .auth-btn:active {
            transform: scale(0.98);
        }

        .auth-switch {
            margin-top: 20px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .auth-switch a {
            color: var(--accent-terracotta);
            text-decoration: none;
            font-weight: bold;
        }

        /* Sistema de Abas Minimalistas */
        .nav-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 25px;
            width: 100%;
            max-width: 600px;
            overflow-x: auto;
            padding-bottom: 8px;
            scrollbar-width: none;
        }

        .nav-tabs::-webkit-scrollbar {
            display: none;
        }

        .tab-btn {
            background-color: #EFE6D8;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-main);
            white-space: nowrap;
            font-size: 0.85rem;
            flex-shrink: 0;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .tab-btn.active {
            background-color: var(--accent-terracotta);
            color: white;
            box-shadow: 0 4px 10px rgba(212, 106, 67, 0.2);
        }

        .tab-content {
            display: none;
            width: 100%;
            max-width: 600px;
        }

        .tab-content.active {
            display: block;
        }

        /* Board da Rotina */
        .board {
            display: flex;
            flex-direction: column;
            gap: 15px;
            width: 100%;
        }

        .column {
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 16px;
            padding: 15px;
            border: 1px solid var(--border-color);
        }

        .column h2 {
            font-size: 1.1rem;
            margin-top: 0;
            margin-bottom: 12px;
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: space-between;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .card {
            background-color: var(--card-bg);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 6px rgba(61,38,28,0.03);
            border-left: 5px solid var(--accent-peach);
        }

        .column-foco .card { border-left-color: var(--accent-terracotta); }
        .column-concluido .card { border-left-color: var(--accent-green); opacity: 0.6; }

        .card p { margin: 0 0 10px 0; font-size: 0.95rem; line-height: 1.4; }
        .card-actions { display: flex; justify-content: flex-end; gap: 8px; }

        .btn-action {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 0.8rem;
            padding: 10px 14px;
            border-radius: 8px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-move { background-color: #F3EAE0; color: var(--text-main); }
        .btn-done { background-color: rgba(129, 178, 154, 0.2); color: #4f7a64; }
        .btn-delete { background-color: rgba(212, 106, 67, 0.1); color: var(--accent-terracotta); }

        .quick-capture { width: 100%; margin-bottom: 20px; }
        .quick-capture form { display: flex; gap: 8px; }
        .quick-capture input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 2px solid var(--border-color);
            border-radius: 12px;
            font-size: 1rem;
            outline: none;
            background-color: var(--card-bg);
        }
        .quick-capture button {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 0 18px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Layout SMART, Mídia, Saúde e Finanças */
        .smart-container, .fin-column, .resumo-box, .filtro-box, .saude-box {
            background-color: var(--card-bg);
            padding: 15px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            margin-bottom: 15px;
        }

        /* Visualizador de Tempo / Dashboard de Metas */
        .smart-dashboard {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }

        .dashboard-card {
            flex: 1;
            background: linear-gradient(135deg, #FFF9F6, #FDF0EA);
            border: 1px solid var(--accent-peach);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(212, 106, 67, 0.04);
        }

        .dashboard-card h4 {
            margin: 0;
            font-size: 0.8rem;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }

        .dashboard-card .counter {
            font-size: 2rem;
            font-weight: 800;
            color: var(--accent-terracotta);
            margin: 8px 0 0 0;
        }

        .smart-header-guide {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 4px;
            margin-bottom: 15px;
        }

        .smart-badge {
            text-align: center;
            padding: 6px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.7rem;
            color: white;
            text-transform: uppercase;
        }

        .badge-s { background-color: #5C3D2E; }
        .badge-m { background-color: #8C533C; }
        .badge-a { background-color: #BE785C; }
        .badge-r { background-color: #D49077; }
        .badge-t { background-color: #E6B6A5; }

        .form-section {
            border: 1px solid var(--border-color);
            padding: 12px;
            border-radius: 8px;
            background-color: #FAF9F6;
            margin-bottom: 12px;
        }

        .form-section h3 { font-size: 0.9rem; margin-top: 0; color: var(--accent-terracotta); text-transform: uppercase; letter-spacing: 1px; }

        .form-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
        .form-group label { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); }
        .form-group input, .form-group textarea, .form-group select {
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.9rem;
        }

        .btn-submit-smart, .btn-submit-saude {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
        }

        .btn-submit-saude {
            background-color: var(--accent-green);
        }

        .active-goals-list {
            margin-top: 20px;
        }

        .goal-item, .saude-item-box {
            background-color: #FAF9F6;
            border-left: 6px solid var(--accent-terracotta);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border: 1px solid var(--border-color);
            border-left-width: 6px;
        }

        .saude-item-box {
            border-left-color: var(--accent-blue);
        }

        .goal-item-header, .saude-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .goal-title, .saude-item-title {
            font-size: 1.05rem;
            font-weight: bold;
            color: var(--accent-terracotta);
            margin: 0;
        }

        .saude-item-title {
            color: var(--text-main);
        }

        .goal-grid, .saude-grid {
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 0.85rem;
        }

        .goal-sub-box, .saude-sub-box {
            background: white;
            padding: 10px;
            border-radius: 6px;
            border: 1px dashed var(--border-color);
        }

        .goal-sub-box strong, .saude-sub-box strong {
            color: var(--text-main);
            display: block;
            margin-bottom: 4px;
            font-size: 0.75rem;
            text-transform: uppercase;
        }

        /* Estilos Finanças */
        .fin-form, .shelf-form, .saude-form {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 15px;
        }
        .fin-form input, .shelf-form input, .shelf-form select, .fin-form select, .saude-form select, .saude-form input {
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-size: 0.95rem;
        }
        .fin-form button, .shelf-form button {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
        }

        .fin-item, .media-item, .saude-list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px dashed var(--border-color);
            font-size: 0.9rem;
        }

        .resumo-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            font-weight: 500;
        }

        .saldo-final-box {
            margin-top: 10px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }

        .saldo-positivo {
            background-color: rgba(129, 178, 154, 0.2);
            color: #3b634e;
            border: 1px solid var(--accent-green);
        }

        .saldo-negativo {
            background-color: rgba(224, 122, 95, 0.15);
            color: #a64b32;
            border: 1px solid var(--accent-red);
        }

        .filtro-impulso {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 15px;
        }

        .filtro-box h3, .saude-section-title {
            margin-top: 0;
            font-size: 0.95rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .filtro-box form {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }

        .filtro-box input {
            flex: 1;
            padding: 8px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
        }

        .filtro-box button {
            background: var(--text-main);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
        }

        .top5-box {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
        }
        .top5-box h3 { margin-top:0; border-bottom:1px solid var(--border-color); padding-bottom:5px; text-transform: uppercase; letter-spacing: 1px; }

        .stars { color: var(--star-color); font-weight: bold; }

        /* Estilos de Hábitos Diários Aba Saúde */
        .habitos-diarios-container {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }

        .habitos-card {
            flex: 1;
            background: #F0F7F4;
            border: 1px solid var(--accent-green);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
        }

        .habitos-card.agua {
            background: #EDF6F9;
            border-color: var(--accent-blue);
        }

        .habitos-btn-group {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 10px;
        }

        .habitos-btn {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 5px 12px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>

    {% if not session.get('user_id') %}
        <div class="auth-container">
            <h2 class="auth-title">ORGANIZA<span>MENTE</span></h2>
            <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 20px; letter-spacing: 0.5px;">Organização inteligente para mentes dinâmicas.</p>
            
            {% if request.args.get('register') %}
                <form action="/register" method="POST" class="auth-form">
                    <input type="text" name="username" class="auth-input" placeholder="Criar Usuário" required autocomplete="off">
                    <input type="password" name="password" class="auth-input" placeholder="Criar Senha" required>
                    <button type="submit" class="auth-btn">CRIAR MINHA CONTA</button>
                </form>
                <div class="auth-switch">Já tem conta? <a href="/">Fazer Login</a></div>
            {% else %}
                <form action="/login" method="POST" class="auth-form">
                    <input type="text" name="username" class="auth-input" placeholder="Usuário" required autocomplete="off">
                    <input type="password" name="password" class="auth-input" placeholder="Senha" required>
                    <button type="submit" class="auth-btn">ENTRAR NO ESPAÇO CALMO</button>
                </form>
                <div class="auth-switch">Novo por aqui? <a href="/?register=true">Criar uma Conta</a></div>
            {% endif %}
            
            {% if request.args.get('error') %}
                <p style="color: var(--accent-red); font-size:0.85rem; margin-top: 15px; font-weight:bold;">
                    {% if request.args.get('error') == 'auth' %} Usuário ou senha incorretos!
                    {% elif request.args.get('error') == 'exists' %} Este nome de usuário já está em uso!
                    {% endif %}
                </p>
            {% endif %}
        </div>
    {% else %}
        
        <header>
            <h1>ORGANIZA<span>MENTE</span></h1>
            <a href="/logout" class="user-badge">SAIR (@{{ session.get('username') }})</a>
        </header>

        <div class="nav-tabs">
            <button class="tab-btn active" id="btn-diario" onclick="switchTab('diario')">Rotina</button>
            <button class="tab-btn" id="btn-smart" onclick="switchTab('smart')">SMART</button>
            <button class="tab-btn" id="btn-saude" onclick="switchTab('saude')">Saúde</button>
            <button class="tab-btn" id="btn-midia" onclick="switchTab('midia')">Leituras</button>
            <button class="tab-btn" id="btn-financeiro" onclick="switchTab('financeiro')">Finanças</button>
        </div>

        <div id="tab-diario" class="tab-content active">
            <section class="quick-capture">
                <form action="/add" method="POST">
                    <input type="text" name="task_text" placeholder="Escreva e aperte Enviar..." required autocomplete="off">
                    <button type="submit">Guardar</button>
                </form>
            </section>

            <main class="board">
                <div class="column column-dump">
                    <h2>Esvaziar a Cabeça</h2>
                    {% for task in dados.brain_dump %}
                    <div class="card">
                        <p>{{ task.texto }}</p>
                        <div class="card-actions">
                            <a href="/move/{{ task.id }}/foco_hoje"><button class="btn-action btn-move">Focar</button></a>
                            <a href="/delete/{{ task.id }}"><button class="btn-action btn-delete">Remover</button></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="column column-foco">
                    <h2>Foco de Hoje ({{ dados.foco_hoje|length }}/3)</h2>
                    {% if dados.foco_hoje|length == 0 %}
                        <p style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; padding: 10px 0;">Nenhum foco selecionado.</p>
                    {% endif %}
                    {% for task in dados.foco_hoje %}
                    <div class="card">
                        <p>{{ task.texto }}</p>
                        <div class="card-actions">
                            <a href="/move/{{ task.id }}/concluido"><button class="btn-action btn-done">Feito! 🎉</button></a>
                            <a href="/move/{{ task.id }}/brain_dump"><button class="btn-action btn-move">Voltar</button></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="column column-concluido">
                    <h2>Concluído</h2>
                    {% for task in dados.concluido %}
                    <div class="card">
                        <p>{{ task.texto }}</p>
                        <div class="card-actions">
                            <a href="/delete/{{ task.id }}"><button class="btn-action btn-delete">Limpar</button></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </main>
        </div>

        <div id="tab-smart" class="tab-content">
            <div class="smart-container">
                <div class="smart-dashboard">
                    <div class="dashboard-card">
                        <h4>Metas do Mês</h4>
                        <p class="counter">{{ dados.metas_mes_count }}</p>
                    </div>
                    <div class="dashboard-card">
                        <h4>Metas do Ano</h4>
                        <p class="counter">{{ dados.metas_ano_count }}</p>
                    </div>
                </div>

                <div class="smart-header-guide">
                    <div class="smart-badge badge-s">S</div>
                    <div class="smart-badge badge-m">M</div>
                    <div class="smart-badge badge-a">A</div>
                    <div class="smart-badge badge-r">R</div>
                    <div class="smart-badge badge-t">T</div>
                </div>

                <h2 style="margin-top:0; color: var(--accent-terracotta); text-transform: uppercase; font-size: 1.25rem; letter-spacing: 1px;">Nova Meta SMART</h2>
                <form action="/add_smart" method="POST" class="smart-form">
                    <div class="form-section">
                        <h3>1. Definir a Meta</h3>
                        <div class="form-group">
                            <label>O que você quer alcançar? (Seja específico)</label>
                            <input type="text" name="goal_name" placeholder="Ex: Organizar closet para consignment" required>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3>2. Passos Mensuráveis</h3>
                        <div class="form-group">
                            <label>Passo 1 (Ação Prática):</label>
                            <input type="text" name="step1_desc" placeholder="Ação" required>
                        </div>
                        <div class="form-row" style="display: flex; gap: 8px; margin-top: 5px;">
                            <div class="form-group" style="flex: 1;">
                                <label>Tempo</label>
                                <input type="text" name="step1_time" placeholder="Ex: 1 hora">
                            </div>
                            <div class="form-group" style="flex: 1;">
                                <label>Prazo</label>
                                <input type="date" name="step1_deadline" required>
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3>3. Plano Antifracasso</h3>
                        <div class="form-group">
                            <label>Possível Obstáculo:</label>
                            <textarea name="obstacles" style="height: 50px;" placeholder="Ex: Ficar escolhendo demais e perder o foco..."></textarea>
                        </div>
                        <div class="form-group">
                            <label>Como vou superar esse obstacle?</label>
                            <textarea name="plan_obstacles" style="height: 50px;" placeholder="Ex: Definir despertador de 20 minutos por lote..."></textarea>
                        </div>
                    </div>

                    <button type="submit" class="btn-submit-smart">Salvar Meta SMART</button>
                </form>

                <div class="active-goals-list">
                    <h3 style="color: var(--accent-terracotta); border-bottom: 2px solid var(--accent-peach); padding-bottom: 5px; text-transform: uppercase; font-size: 1.1rem; letter-spacing: 1px;">Minhas Metas</h3>
                    {% if dados.metas_smart|length == 0 %}
                        <p style="font-style: italic; color: var(--text-muted);">Nenhuma meta SMART cadastrada ainda.</p>
                    {% endif %}
                    {% for meta in dados.metas_smart %}
                    <div class="goal-item">
                        <div class="goal-item-header">
                            <h4 class="goal-title">{{ meta.goal_name }}</h4>
                            <a href="/delete_smart/{{ meta.id }}"><button class="btn-action btn-delete">Excluir</button></a>
                        </div>
                        <div class="goal-grid">
                            <div class="goal-sub-box">
                                <strong>Passo Prático</strong>
                                {{ meta.step1_desc }} ({{ meta.step1_time }}) - 
                                Prazo: 
                                {% if meta.step1_deadline %}
                                    {{ meta.step1_deadline[8:10] }}/{{ meta.step1_deadline[5:7] }}/{{ meta.step1_deadline[0:4] }}
                                {% else %}
                                    Não definido
                                {% endif %}
                            </div>
                            {% if meta.obstacles %}
                            <div class="goal-sub-box">
                                <strong>Plano Contra Obstáculos</strong>
                                <span style="color: var(--accent-red)">Obs:</span> {{ meta.obstacles }} <br>
                                <span style="color: var(--accent-green)">Plano:</span> {{ meta.plan_obstacles }}
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div id="tab-saude" class="tab-content">
            
            <div class="habitos-diarios-container">
                <div class="habitos-card agua">
                    <h4 style="color: #31572C;">Meta de Água 💧</h4>
                    <p style="font-size: 1.8rem; font-weight: 800; margin: 5px 0;" id="agua-contador">{{ dados.usuario.copos_agua }} / 8 copos</p>
                    <div class="habitos-btn-group">
                        <a href="/update_agua/-1" style="text-decoration:none;"><button class="habitos-btn">-</button></a>
                        <a href="/update_agua/1" style="text-decoration:none;"><button class="habitos-btn" style="background:var(--accent-blue); border-color:#90e0ef;">+ Bebi Copo</button></a>
                    </div>
                </div>

                <div class="habitos-card">
                    <h4 style="color: #2F5233;">Exercício Físico 💪</h4>
                    <p style="font-size: 1.1rem; font-weight: bold; margin: 10px 0 5px 0;">
                        {% if dados.usuario.exercicio_feito %}
                            Feito hoje! 🎉
                        {% else %}
                            Ainda pendente 🏃‍♀️
                        {% endif %}
                    </p>
                    <div class="habitos-btn-group">
                        <a href="/toggle_exercicio" style="text-decoration:none;">
                            <button class="habitos-btn" style="{% if dados.usuario.exercicio_feito %}background:var(--accent-green); color:white;{% endif %}">
                                {% if dados.usuario.exercicio_feito %}Concluído{% else %}Marcar como Feito{% endif %}
                            </button>
                        </a>
                    </div>
                </div>
            </div>

            <div class="saude-box">
                <h2 style="margin-top:0; color: var(--accent-green); text-transform: uppercase; font-size: 1.1rem; letter-spacing: 1px;">Adicionar à Rotina de Saúde</h2>
                <form action="/add_saude" method="POST" class="saude-form">
                    <input type="text" name="titulo" placeholder="Descrição (Ex: Terapia com Roberta, Ritalina, Hemograma)" required>
                    <select name="categoria" required>
                        <option value="terapia">Terapia</option>
                        <option value="exames">Exame de Sangue / Consultas</option>
                        <option value="medicamento">Medicamentos</option>
                    </select>
                    
                    <div style="display:flex; gap:8px;">
                        <input type="date" name="data" style="flex:1;">
                        <input type="time" name="hora" style="flex:1;">
                    </div>
                    
                    <select name="status" required>
                        <option value="agendado">Agendado / Pendente</option>
                        <option value="concluido">Concluído</option>
                    </select>
                    <button type="submit" class="btn-submit-saude">Adicionar à Rotina</button>
                </form>
            </div>

            <div class="saude-box">
                <h3 class="saude-section-title" style="color: var(--accent-terracotta);">Terapia & Consultas</h3>
                {% for item in dados.saude if item.categoria in ['terapia', 'exames'] %}
                <div class="saude-list-item">
                    <span>
                        <a href="/toggle_saude/{{ item.id }}" style="text-decoration:none; margin-right:8px; font-size:1.1rem;">
                            {% if item.status == 'concluido' %}✅{% else %}⬜{% endif %}
                        </a>
                        <strong style="{% if item.status == 'concluido' %}text-decoration:line-through; color:var(--text-muted);{% endif %}">
                            [{{ item.categoria | capitalize }}] {{ item.titulo }}
                        </strong>
                        <br>
                        <small style="color:var(--text-muted); padding-left:26px;">
                            Data: {% if item.data %}{{ item.data[8:10] }}/{{ item.data[5:7] }}{% else %}Não definida{% endif %} às {{ item.hora or '--:--' }}
                        </small>
                    </span>
                    <a href="/delete_saude/{{ item.id }}" style="color:var(--accent-red); text-decoration:none; font-size:0.85rem;">Remover</a>
                </div>
                {% endfor %}
            </div>

            <div class="saude-box">
                <h3 class="saude-section-title" style="color: var(--accent-green);">Medicamentos de Uso Contínuo</h3>
                {% for item in dados.saude if item.categoria == 'medicamento' %}
                <div class="saude-list-item">
                    <span>
                        <a href="/toggle_saude/{{ item.id }}" style="text-decoration:none; margin-right:8px; font-size:1.1rem;">
                            {% if item.status == 'concluido' %}💊 Concluído{% else %}⬜ Tomar{% endif %}
                        </a>
                        <strong style="{% if item.status == 'concluido' %}text-decoration:line-through; color:var(--text-muted);{% endif %}">
                            {{ item.titulo }}
                        </strong>
                        <br>
                        <small style="color:var(--text-muted); padding-left:26px;">
                            Horário cadastrado: {{ item.hora or 'Não definido' }}
                        </small>
                    </span>
                    <a href="/delete_saude/{{ item.id }}" style="color:var(--accent-red); text-decoration:none; font-size:0.85rem;">Remover</a>
                </div>
                {% endfor %}
            </div>
        </div>

        <div id="tab-midia" class="tab-content">
            <div class="fin-column">
                <h2 class="fin-title" style="text-transform: uppercase; letter-spacing: 1px; font-size: 1.1rem;">Leituras e Filmes do Ano</h2>
                <form action="/add_media" method="POST" class="shelf-form">
                    <input type="text" name="titulo" placeholder="Título..." required>
                    <input type="text" name="autor" placeholder="Autor / Diretor..." required>
                    <select name="tipo" required>
                        <option value="livros">Livro</option>
                        <option value="filmes">Filme</option>
                    </select>
                    <select name="nota" required>
                        <option value="5">⭐⭐⭐⭐⭐</option>
                        <option value="4">⭐⭐⭐⭐</option>
                        <option value="3">⭐⭐⭐</option>
                    </select>
                    <button type="submit">Adicionar Mídia</button>
                </form>

                <div>
                    {% for midia in dados.midias %}
                    <div class="media-item">
                        <span>
                            <a href="/toggle_media/{{ midia.id }}" style="text-decoration:none; margin-right:8px;">
                                {% if midia.concluido %}✅{% else %}⬜{% endif %}
                            </a>
                            <strong style="{% if midia.concluido %}text-decoration:line-through; color:var(--text-muted);{% endif %}">{{ midia.titulo }}</strong>
                        </span>
                        <span>
                            <span class="stars">{% for i in range(midia.nota) %}★{% endfor %}</span>
                            <a href="/delete_media/{{ midia.id }}" style="text-decoration:none; margin-left:12px;">Remover</a>
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div id="tab-financeiro" class="tab-content">
            
            <div class="resumo-box" style="margin-bottom:15px; border-color: var(--accent-peach);">
                <h3 style="margin-top:0; color:var(--accent-terracotta); text-transform: uppercase; font-size:0.9rem; letter-spacing:0.5px;">Visualizar Mês Vigente</h3>
                <form action="/selecionar_mes" method="POST" style="display:flex; gap:10px;">
                    <select name="mes" style="flex:1; padding:8px; border-radius:8px; border:1px solid var(--border-color);">
                        <option value="1" {% if dados.mes_atual == 1 %}selected{% endif %}>Janeiro</option>
                        <option value="2" {% if dados.mes_atual == 2 %}selected{% endif %}>Fevereiro</option>
                        <option value="3" {% if dados.mes_atual == 3 %}selected{% endif %}>Março</option>
                        <option value="4" {% if dados.mes_atual == 4 %}selected{% endif %}>Abril</option>
                        <option value="5" {% if dados.mes_atual == 5 %}selected{% endif %}>Maio</option>
                        <option value="6" {% if dados.mes_atual == 6 %}selected{% endif %}>Junho</option>
                        <option value="7" {% if dados.mes_atual == 7 %}selected{% endif %}>Julho</option>
                        <option value="8" {% if dados.mes_atual == 8 %}selected{% endif %}>Agosto</option>
                        <option value="9" {% if dados.mes_atual == 9 %}selected{% endif %}>Setembro</option>
                        <option value="10" {% if dados.mes_atual == 10 %}selected{% endif %}>Outubro</option>
                        <option value="11" {% if dados.mes_atual == 11 %}selected{% endif %}>Novembro</option>
                        <option value="12" {% if dados.mes_atual == 12 %}selected{% endif %}>Dezembro</option>
                    </select>
                    <select name="ano" style="width:100px; padding:8px; border-radius:8px; border:1px solid var(--border-color);">
                        <option value="2025" {% if dados.ano_atual == 2025 %}selected{% endif %}>2025</option>
                        <option value="2026" {% if dados.ano_atual == 2026 %}selected{% endif %}>2026</option>
                        <option value="2027" {% if dados.ano_atual == 2027 %}selected{% endif %}>2027</option>
                    </select>
                    <button type="submit" style="background:var(--accent-terracotta); border:none; color:white; padding:8px 15px; border-radius:8px; font-weight:bold; cursor:pointer;">Ir</button>
                </form>
            </div>

            <div class="resumo-box">
                <h3 class="resumo-title" style="text-transform: uppercase; letter-spacing: 1px; font-size: 1.1rem; color: var(--accent-terracotta);">
                    Resumo de {{ dados.nome_mes_atual }}/{{ dados.ano_atual }}
                </h3>
                
                <div class="resumo-row">
                    <span>Saldo Inicial (Mês Anterior):</span>
                    <form action="/update_saldo_inicial" method="POST" style="display:flex; gap:5px;">
                        <input type="hidden" name="mes" value="{{ dados.mes_atual }}">
                        <input type="hidden" name="ano" value="{{ dados.ano_atual }}">
                        <input type="number" step="0.01" name="saldo" value="{{ dados.saldo_inicial }}" style="width:75px; border-radius:4px; border:1px solid var(--border-color); text-align:center; padding: 4px;">
                        <button type="submit" style="font-size:0.7rem; background: var(--accent-terracotta); border:none; color:white; padding:4px 8px; border-radius:4px; font-weight:bold; cursor:pointer;">ok</button>
                    </form>
                </div>

                <div class="resumo-row"><span>Total Entradas:</span><span style="color:var(--accent-green); font-weight:bold;">R$ {{ "%.2f"|format(dados.total_entradas) }}</span></div>
                <div class="resumo-row"><span>Gastos Fixos:</span><span style="color:var(--accent-red); font-weight:bold;">R$ {{ "%.2f"|format(dados.total_fixos) }}</span></div>
                <div class="resumo-row"><span>Gastos Variáveis:</span><span style="color:var(--accent-red); font-weight:bold;">R$ {{ "%.2f"|format(dados.total_variaveis) }}</span></div>

                {% if dados.saldo_final >= 0 %}
                <div class="saldo-final-box saldo-positivo">Sobra: R$ {{ "%.2f"|format(dados.saldo_final) }}</div>
                {% else %}
                <div class="saldo-final-box saldo-negativo">Falta: R$ {{ "%.2f"|format(dados.saldo_final) }}</div>
                {% endif %}
            </div>

            <div class="fin-column">
                <h2 class="fin-title" style="text-transform: uppercase; letter-spacing: 1px; font-size: 1.1rem; color: var(--accent-terracotta);">Lançar Transação</h2>
                <form action="/add_financeiro" method="POST" class="fin-form">
                    <input type="hidden" name="mes" value="{{ dados.mes_atual }}">
                    <input type="hidden" name="ano" value="{{ dados.ano_atual }}">
                    <input type="text" name="desc" placeholder="Descrição..." required>
                    <input type="number" step="0.01" name="valor" placeholder="Valor (R$)" required>
                    <select name="tipo" required>
                        <option value="entradas">Entrada (Salário, VR...)</option>
                        <option value="gastos_fixos">Gasto Fixo (Contas)</option>
                        <option value="gastos_variaveis">Gasto Variável (Cartão...)</option>
                    </select>
                    <button type="submit">Salvar Registro</button>
                </form>

                <div class="fin-list">
                    {% for item in dados.financeiro %}
                    <div class="fin-item">
                        <span>{{ item.descricao }}</span>
                        <span style="font-weight:bold; {% if item.tipo == 'entradas' %}color:var(--accent-green);{% else %}color:var(--text-main);{% endif %}">
                            R$ {{ "%.2f"|format(item.valor) }}
                            <a href="/delete_financeiro/{{ item.id }}" style="text-decoration:none; margin-left:8px;">Remover</a>
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="filtro-impulso">
                <div class="filtro-box">
                    <h3 style="color:var(--accent-terracotta)">Quero (Desejo)</h3>
                    <form action="/add_impulso/quero" method="POST">
                        <input type="text" name="item" placeholder="Ex: Videgame" style="flex:2;" required>
                        <input type="number" step="0.01" name="valor_previsto" placeholder="Previsão R$" style="flex:1;" required>
                        <button type="submit">+</button>
                    </form>
                    <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                        {% for item in dados.desejos if item.tipo == 'quero' %}
                        <li style="margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span>{{ item.item }} <span style="color:var(--text-muted); font-style:italic;">(R$ {{ "%.2f"|format(item.valor_previsto) }})</span></span>
                            <a href="/delete_impulso/{{ item.id }}" style="color:var(--accent-red); text-decoration:none;">Remover</a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="filtro-box">
                    <h3 style="color:var(--accent-green)">Preciso (Necessidade)</h3>
                    <form action="/add_impulso/preciso" method="POST">
                        <input type="text" name="item" placeholder="Ex: Dentista" style="flex:2;" required>
                        <input type="number" step="0.01" name="valor_previsto" placeholder="Previsão R$" style="flex:1;" required>
                        <button type="submit">+</button>
                    </form>
                    <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                        {% for item in dados.desejos if item.tipo == 'preciso' %}
                        <li style="margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span>{{ item.item }} <span style="color:var(--text-muted); font-style:italic;">(R$ {{ "%.2f"|format(item.valor_previsto) }})</span></span>
                            <a href="/delete_impulso/{{ item.id }}" style="color:var(--accent-red); text-decoration:none;">Remover</a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    {% endif %}

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(function(content) {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });

            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('btn-' + tabName).classList.add('active');
        }

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
    </script>
</body>
</html>
'''

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template_string(HTML_TEMPLATE, dados=None)
    
    user_id = session['user_id']
    ano_atual = int(session.get('financeiro_ano', datetime.now().year))
    mes_atual = int(session.get('financeiro_mes', datetime.now().month))
    
    conn = obter_conexao()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    
    # Busca tarefas
    tarefas_db = conn.execute('SELECT * FROM tarefas WHERE user_id = ?', (user_id,)).fetchall()
    brain_dump = [t for t in tarefas_db if t['coluna'] == 'brain_dump']
    foco_hoje = [t for t in tarefas_db if t['coluna'] == 'foco_hoje']
    concluido = [t for t in tarefas_db if t['coluna'] == 'concluido']
    
    # Busca metas SMART
    metas_smart = conn.execute('SELECT * FROM metas_smart WHERE user_id = ? ORDER BY step1_deadline ASC', (user_id,)).fetchall()
    
    hoje_data = datetime.now()
    metas_mes_count = 0
    metas_ano_count = 0
    for meta in metas_smart:
        if meta['step1_deadline']:
            try:
                dt_meta = datetime.strptime(meta['step1_deadline'], '%Y-%m-%d')
                if dt_meta.year == hoje_data.year:
                    metas_ano_count += 1
                    if dt_meta.month == hoje_data.month:
                        metas_mes_count += 1
            except ValueError:
                pass

    # Busca mídias
    midias = conn.execute('SELECT * FROM mídias WHERE user_id = ?', (user_id,)).fetchall()
    
    # Busca financeiro
    financeiro = conn.execute(
        'SELECT * FROM financeiro WHERE user_id = ? AND ano = ? AND mes = ?', 
        (user_id, ano_atual, mes_atual)
    ).fetchall()
    
    # Busca desejos
    desejos = conn.execute('SELECT * FROM desejos WHERE user_id = ?', (user_id,)).fetchall()

    # Busca Saúde Checkup
    saude = conn.execute('SELECT * FROM saude_checkup WHERE user_id = ? ORDER BY data ASC, hora ASC', (user_id,)).fetchall()
    
    # Lógica de Saldo Acumulado
    saldo_man = conn.execute(
        'SELECT valor FROM saldos_iniciais WHERE user_id = ? AND ano = ? AND mes = ?', 
        (user_id, ano_atual, mes_atual)
    ).fetchone()

    if saldo_man:
        saldo_inicial = saldo_man['valor']
    else:
        if mes_atual == 1:
            prev_mes, prev_ano = 12, ano_atual - 1
        else:
            prev_mes, prev_ano = mes_atual - 1, ano_atual
        
        saldo_inicial = obter_sobra_mes(conn, user_id, prev_ano, prev_mes)

    total_entradas = sum(f['valor'] for f in financeiro if f['tipo'] == 'entradas')
    total_fixos = sum(f['valor'] for f in financeiro if f['tipo'] == 'gastos_fixos')
    total_variaveis = sum(f['valor'] for f in financeiro if f['tipo'] == 'gastos_variaveis')
    saldo_final = saldo_inicial + total_entradas - (total_fixos + total_variaveis)

    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    conn.close()
    
    dados = {
        "usuario": usuario,
        "brain_dump": brain_dump,
        "foco_hoje": foco_hoje,
        "concluido": concluido,
        "metas_smart": metas_smart,
        "metas_mes_count": metas_mes_count,
        "metas_ano_count": metas_ano_count,
        "midias": midias,
        "financeiro": financeiro,
        "desejos": desejos,
        "saude": saude,
        "meta_livros_quero": usuario['meta_livros'],
        "meta_filmes_quero": usuario['meta_filmes'],
        "mes_atual": mes_atual,
        "ano_atual": ano_atual,
        "nome_mes_atual": meses_pt.get(mes_atual, ""),
        "saldo_inicial": saldo_inicial,
        "total_entradas": total_entradas,
        "total_fixos": total_fixos,
        "total_variaveis": total_variaveis,
        "saldo_final": saldo_final
    }
    
    return render_template_string(HTML_TEMPLATE, dados=dados)

# --- ROTAS DA ABA SAÚDE ---

@app.route('/add_saude', methods=['POST'])
def add_saude():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('''
        INSERT INTO saude_checkup (user_id, titulo, categoria, data, hora, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        request.form.get("titulo"),
        request.form.get("categoria"),
        request.form.get("data"),
        request.form.get("hora"),
        request.form.get("status")
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/toggle_saude/<int:item_id>')
def toggle_saude(item_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    item = conn.execute('SELECT status FROM saude_checkup WHERE id = ?', (item_id,)).fetchone()
    if item:
        novo_status = 'concluido' if item['status'] == 'agendado' else 'agendado'
        conn.execute('UPDATE saude_checkup SET status = ? WHERE id = ? AND user_id = ?', (novo_status, item_id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_saude/<int:item_id>')
def delete_saude(item_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM saude_checkup WHERE id = ? AND user_id = ?', (item_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_agua/<int:valor>')
def update_agua(valor):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    user = conn.execute('SELECT copos_agua FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    if user:
        novos_copos = max(0, user['copos_agua'] + valor)
        conn.execute('UPDATE usuarios SET copos_agua = ? WHERE id = ?', (novos_copos, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/toggle_exercicio')
def toggle_exercicio():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    user = conn.execute('SELECT exercicio_feito FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    if user:
        novo_status = 1 - user['exercicio_feito']
        conn.execute('UPDATE usuarios SET exercicio_feito = ? WHERE id = ?', (novo_status, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- OUTRAS ROTAS ---

@app.route('/selecionar_mes', methods=['POST'])
def selecionar_mes():
    if 'user_id' not in session: return redirect(url_for('index'))
    session['financeiro_mes'] = int(request.form.get("mes"))
    session['financeiro_ano'] = int(request.form.get("ano"))
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username').strip().lower()
    password = request.form.get('password')
    
    conn = obter_conexao()
    user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and user['password'] == hash_senha(password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['financeiro_mes'] = datetime.now().month
        session['financeiro_ano'] = datetime.now().year
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', error='auth'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username').strip().lower()
    password = request.form.get('password')
    
    conn = obter_conexao()
    existente = conn.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
    if existente:
        conn.close()
        return redirect(url_for('index', register=True, error='exists'))
    
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, hash_senha(password)))
    conn.commit()
    
    user_id = cursor.lastrowid
    conn.close()
    
    session['user_id'] = user_id
    session['username'] = username
    session['financeiro_mes'] = datetime.now().month
    session['financeiro_ano'] = datetime.now().year
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- ROTAS DE TAREFAS ---

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session: return redirect(url_for('index'))
    task_text = request.form.get('task_text')
    if task_text:
        conn = obter_conexao()
        conn.execute('INSERT INTO tarefas (user_id, texto, coluna) VALUES (?, ?, ?)', (session['user_id'], task_text, 'brain_dump'))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/move/<int:task_id>/<coluna>')
def move_task(task_id, coluna):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('UPDATE tarefas SET coluna = ? WHERE id = ? AND user_id = ?', (coluna, task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM tarefas WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- ROTAS SMART ---

@app.route('/add_smart', methods=['POST'])
def add_smart():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('''
        INSERT INTO metas_smart (user_id, goal_name, step1_desc, step1_time, step1_deadline, obstacles, plan_obstacles)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'], 
        request.form.get("goal_name"), 
        request.form.get("step1_desc"), 
        request.form.get("step1_time"), 
        request.form.get("step1_deadline"),
        request.form.get("obstacles"),
        request.form.get("plan_obstacles")
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_smart/<int:meta_id>')
def delete_smart(meta_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM metas_smart WHERE id = ? AND user_id = ?', (meta_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- ROTAS DE FILMES/LIVROS ---

@app.route('/add_media', methods=['POST'])
def add_media():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('''
        INSERT INTO mídias (user_id, titulo, autor, nota, tipo, concluido)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (session['user_id'], request.form.get("titulo"), request.form.get("autor"), int(request.form.get("nota")), request.form.get("tipo")))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/toggle_media/<int:media_id>')
def toggle_media(media_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('UPDATE mídias SET concluido = 1 - concluido WHERE id = ? AND user_id = ?', (media_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_media/<int:media_id>')
def delete_media(media_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM mídias WHERE id = ? AND user_id = ?', (media_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- ROTAS FINANCEIRAS ---

@app.route('/add_financeiro', methods=['POST'])
def add_financeiro():
    if 'user_id' not in session: return redirect(url_for('index'))
    mes = int(request.form.get("mes"))
    ano = int(request.form.get("ano"))
    conn = obter_conexao()
    conn.execute('''
        INSERT INTO financeiro (user_id, descricao, valor, tipo, ano, mes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], request.form.get("desc"), float(request.form.get("valor")), request.form.get("tipo"), ano, mes))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_financeiro/<int:fin_id>')
def delete_financeiro(fin_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM financeiro WHERE id = ? AND user_id = ?', (fin_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_saldo_inicial', methods=['POST'])
def update_saldo_inicial():
    if 'user_id' not in session: return redirect(url_for('index'))
    saldo = request.form.get("saldo")
    mes = int(request.form.get("mes"))
    ano = int(request.form.get("ano"))
    
    if saldo:
        conn = obter_conexao()
        conn.execute('''
            INSERT INTO saldos_iniciais (user_id, ano, mes, valor)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, ano, mes) DO UPDATE SET valor = excluded.valor
        ''', (session['user_id'], ano, mes, float(saldo)))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/add_impulso/<tipo>', methods=['POST'])
def add_impulso(tipo):
    if 'user_id' not in session: return redirect(url_for('index'))
    item = request.form.get("item")
    valor = request.form.get("valor_previsto")
    if item and tipo in ['quero', 'preciso']:
        conn = obter_conexao()
        conn.execute('''
            INSERT INTO desejos (user_id, item, tipo, valor_previsto) 
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], item, tipo, float(valor) if valor else 0.0))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_impulso/<int:desejo_id>')
def delete_impulso(desejo_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = obter_conexao()
    conn.execute('DELETE FROM desejos WHERE id = ? AND user_id = ?', (desejo_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- OUTROS ARQUIVOS ---

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def service_worker():
    sw_code = """
    self.addEventListener('install', function(e) {
        self.skipWaiting();
    });
    self.addEventListener('fetch', function(e) {
        // Apenas repassa as requisições
    });
    """
    return sw_code, 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    # Para evitar conflitos de cache no primeiro deploy com as novas tabelas de saúde,
    # caso você precise forçar a atualização das tabelas, o banco de dados é ajustado na inicialização
    app.run(debug=True, host='0.0.0.0', port=5000)
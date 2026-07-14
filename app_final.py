# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_dopaminergica' # Requerido para gerenciar sessões de login

DB_FILE = 'organizamente.db'

# --- FUNÇÕES DE BANCO DE DE DADOS ---

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
            saldo_inicial REAL DEFAULT 0.0,
            anotacoes_midia TEXT DEFAULT '',
            meta_livros INTEGER DEFAULT 10,
            meta_filmes INTEGER DEFAULT 20
        )
    ''')
    
    # Tabela de Tarefas (Brain Dump / Foco / Concluído)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            coluna TEXT NOT NULL, -- 'brain_dump', 'foco_hoje', 'concluido'
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
            step2_desc TEXT,
            step2_time TEXT,
            step2_deadline TEXT,
            resources TEXT,
            obstacles TEXT,
            plan_obstacles TEXT,
            success_measurement TEXT,
            achieved_outcome TEXT,
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
            tipo TEXT NOT NULL, -- 'livros' ou 'filmes'
            concluido INTEGER DEFAULT 0, -- 0 para Falso, 1 para Verdadeiro
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
            tipo TEXT NOT NULL, -- 'entradas', 'gastos_fixos', 'gastos_variaveis'
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela Quero vs Preciso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desejos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'quero' ou 'preciso'
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Criptografia simples de senha para segurança básica
def hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# Inicializa o banco de dados antes do primeiro acesso
inicializar_banco()

# --- TEMPLATE HTML COMPLETO (Com Login, Registro e Dashboard adaptado para Mobile) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#D46A43">
    <title>OrganizaMente 🥇</title>
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
            margin-top: 10px;
            margin-bottom: 20px;
            width: 100%;
            max-width: 600px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-size: 1.6rem;
            margin: 0;
            color: var(--accent-terracotta);
            font-weight: 700;
        }

        .user-badge {
            font-size: 0.85rem;
            background-color: var(--accent-peach);
            color: var(--text-main);
            padding: 5px 12px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
        }

        /* Telas de Login e Cadastro */
        .auth-container {
            background-color: var(--card-bg);
            padding: 30px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 15px rgba(61, 38, 28, 0.05);
            width: 100%;
            max-width: 360px;
            margin-top: 50px;
            text-align: center;
        }

        .auth-title {
            color: var(--accent-terracotta);
            margin-bottom: 20px;
            font-size: 1.5rem;
            font-weight: 700;
        }

        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .auth-input {
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            outline: none;
            font-size: 1rem;
        }

        .auth-btn {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
        }

        .auth-switch {
            margin-top: 15px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .auth-switch a {
            color: var(--accent-terracotta);
            text-decoration: none;
            font-weight: bold;
        }

        /* Sistema de Abas */
        .nav-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
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
            padding: 10px 18px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-main);
            white-space: nowrap;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .tab-btn.active {
            background-color: var(--accent-terracotta);
            color: white;
            box-shadow: 0 4px 10px rgba(212, 106, 67, 0.25);
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
            font-size: 1.15rem;
            margin-top: 0;
            margin-bottom: 12px;
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: space-between;
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
            font-size: 0.85rem;
            padding: 10px 14px;
            border-radius: 8px;
            font-weight: 600;
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
        }

        /* Layout SMART, Mídia e Finanças */
        .smart-container, .fin-column, .resumo-box, .filtro-box {
            background-color: var(--card-bg);
            padding: 15px;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            margin-bottom: 15px;
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

        .form-section h3 { font-size: 0.95rem; margin-top: 0; color: var(--accent-terracotta); }

        .form-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
        .form-group label { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); }
        .form-group input, .form-group textarea {
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.9rem;
        }

        .btn-submit-smart {
            background-color: var(--accent-terracotta);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
        }

        .active-goals-list {
            margin-top: 20px;
        }

        .goal-item {
            background-color: #FAF9F6;
            border-left: 6px solid var(--accent-terracotta);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border: 1px solid var(--border-color);
            border-left-width: 6px;
        }

        .goal-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .goal-title {
            font-size: 1.05rem;
            font-weight: bold;
            color: var(--accent-terracotta);
            margin: 0;
        }

        .goal-grid {
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 0.85rem;
        }

        .goal-sub-box {
            background: white;
            padding: 10px;
            border-radius: 6px;
            border: 1px dashed var(--border-color);
        }

        .goal-sub-box strong {
            color: var(--text-main);
            display: block;
            margin-bottom: 4px;
            font-size: 0.75rem;
            text-transform: uppercase;
        }

        /* Estilos Finanças */
        .fin-form, .shelf-form {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 15px;
        }
        .fin-form input, .shelf-form input, .shelf-form select {
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
        }

        .fin-item, .media-item {
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

        .filtro-box h3 {
            margin-top: 0;
            font-size: 0.95rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
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
        }

        .top5-box {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
        }
        .top5-box h3 { margin-top:0; border-bottom:1px solid var(--border-color); padding-bottom:5px; }

        .stars { color: var(--star-color); font-weight: bold; }
    </style>
</head>
<body>

    <!-- SESSÃO DE LOGIN/CADASTRO -->
    {% if not session.get('user_id') %}
        <div class="auth-container">
            <h2 class="auth-title">🥇 OrganizaMente</h2>
            <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 20px;">Organização inteligente para mentes dinâmicas.</p>
            
            {% if request.args.get('register') %}
                <!-- Tela de Cadastro -->
                <form action="/register" method="POST" class="auth-form">
                    <input type="text" name="username" class="auth-input" placeholder="Criar Usuário" required autocomplete="off">
                    <input type="password" name="password" class="auth-input" placeholder="Criar Senha" required>
                    <button type="submit" class="auth-btn">Criar Minha Conta ⚡</button>
                </form>
                <div class="auth-switch">Já tem conta? <a href="/">Fazer Login</a></div>
            {% else %}
                <!-- Tela de Login -->
                <form action="/login" method="POST" class="auth-form">
                    <input type="text" name="username" class="auth-input" placeholder="Usuário" required autocomplete="off">
                    <input type="password" name="password" class="auth-input" placeholder="Senha" required>
                    <button type="submit" class="auth-btn">Entrar no Espaço Calmo 🧠</button>
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
        
        <!-- DASHBOARD MULTIUSUÁRIO AUTENTICADO -->
        <header>
            <h1>OrganizaMente 🥇</h1>
            <a href="/logout" class="user-badge">Sair (@{{ session.get('username') }})</a>
        </header>

        <div class="nav-tabs">
            <button class="tab-btn active" id="btn-diario" onclick="switchTab('diario')">⚡ Rotina</button>
            <button class="tab-btn" id="btn-smart" onclick="switchTab('smart')">🎯 SMART</button>
            <button class="tab-btn" id="btn-midia" onclick="switchTab('midia')">📚 Leituras</button>
            <button class="tab-btn" id="btn-financeiro" onclick="switchTab('financeiro')">💰 Finanças</button>
        </div>

        <!-- ABA 1: ROTINA DIÁRIA -->
        <div id="tab-diario" class="tab-content active">
            <section class="quick-capture">
                <form action="/add" method="POST">
                    <input type="text" name="task_text" placeholder="Escreva e aperte Enviar..." required autocomplete="off">
                    <button type="submit">Guardar</button>
                </form>
            </section>

            <main class="board">
                <!-- Esvaziar a Cabeça -->
                <div class="column column-dump">
                    <h2>📥 Esvaziar a Cabeça</h2>
                    {% for task in dados.brain_dump %}
                    <div class="card">
                        <p>{{ task.texto }}</p>
                        <div class="card-actions">
                            <a href="/move/{{ task.id }}/foco_hoje"><button class="btn-action btn-move">🎯 Focar</button></a>
                            <a href="/delete/{{ task.id }}"><button class="btn-action btn-delete">🗑️</button></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <!-- Foco de Hoje -->
                <div class="column column-foco">
                    <h2>🎯 Foco de Hoje ({{ dados.foco_hoje|length }}/3)</h2>
                    {% if dados.foco_hoje|length == 0 %}
                        <p style="color: var(--text-muted); font-size: 0.9rem; font-style: italic; padding: 10px 0;">Nenhum foco selecionado.</p>
                    {% endif %}
                    {% for task in dados.foco_hoje %}
                    <div class="card">
                        <p>{{ task.texto }}</p>
                        <div class="card-actions">
                            <a href="/move/{{ task.id }}/concluido"><button class="btn-action btn-done">Feito! 🎉</button></a>
                            <a href="/move/{{ task.id }}/brain_dump"><button class="btn-action btn-move">↩️ Voltar</button></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <!-- Concluído -->
                <div class="column column-concluido">
                    <h2>🎉 Concluído</h2>
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

        <!-- ABA 2: PLANEJADOR SMART (VERSÃO COMPLETA E DETALHADA) -->
        <div id="tab-smart" class="tab-content">
            <div class="smart-container">
                <div class="smart-header-guide">
                    <div class="smart-badge badge-s">S - Específica</div>
                    <div class="smart-badge badge-m">M - Mensurável</div>
                    <div class="smart-badge badge-a">A - Atingível</div>
                    <div class="smart-badge badge-r">R - Relevante</div>
                    <div class="smart-badge badge-t">T - Temporal</div>
                </div>

                <h2 style="margin-top:0; color: var(--accent-terracotta);">Nova Meta SMART</h2>
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
                            <label>Passo 1 (Ação Física Prática):</label>
                            <input type="text" name="step1_desc" placeholder="Ação" required>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Tempo</label>
                                <input type="text" name="step1_time" placeholder="30 min">
                            </div>
                            <div class="form-group">
                                <label>Prazo</label>
                                <input type="text" name="step1_deadline" placeholder="Sábado">
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3>3. Plano Antifracasso</h3>
                        <div class="form-group">
                            <label>Possível Obstáculo:</label>
                            <textarea name="obstacles" placeholder="Ex: Ficar escolhendo demais e perder o foco..."></textarea>
                        </div>
                        <div class="form-group">
                            <label>Como vou superar esse obstáculo?</label>
                            <textarea name="plan_obstacles" placeholder="Ex: Definir despertador de 20 minutos por lote de roupa..."></textarea>
                        </div>
                    </div>

                    <button type="submit" class="btn-submit-smart">Salvar Meta SMART 🎯</button>
                </form>

                <div class="active-goals-list">
                    <h3 style="color: var(--accent-terracotta); border-bottom: 2px solid var(--accent-peach); padding-bottom: 5px;">Minhas Metas</h3>
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
                                {{ meta.step1_desc }} ({{ meta.step1_time }}) - Prazo: {{ meta.step1_deadline }}
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

        <!-- ABA 3: FILMES E LEITURAS -->
        <div id="tab-midia" class="tab-content">
            <div class="fin-column">
                <h2 class="fin-title">📚 Leituras e Filmes do Ano</h2>
                <form action="/add_media" method="POST" class="shelf-form">
                    <input type="text" name="titulo" placeholder="Título..." required>
                    <input type="text" name="autor" placeholder="Autor / Diretor..." required>
                    <select name="tipo" required>
                        <option value="livros">Livro 📖</option>
                        <option value="filmes">Filme 🎬</option>
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
                            {% if midia.tipo == 'livros' %}📖{% else %}🎬{% endif %}
                            <strong style="{% if midia.concluido %}text-decoration:line-through; color:var(--text-muted);{% endif %}">{{ midia.titulo }}</strong>
                        </span>
                        <span>
                            <span class="stars">{% for i in range(midia.nota) %}★{% endfor %}</span>
                            <a href="/delete_media/{{ midia.id }}" style="text-decoration:none; margin-left:12px;">🗑️</a>
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- ABA 4: CONTROLE FINANCEIRO -->
        <div id="tab-financeiro" class="tab-content">
            <div class="resumo-box">
                <h3 class="resumo-title">📊 Resumo Mensal</h3>
                
                <div class="resumo-row">
                    <span>Saldo Inicial (Mês Anterior):</span>
                    <form action="/update_saldo_inicial" method="POST" style="display:flex; gap:5px;">
                        <input type="number" step="0.01" name="saldo" value="{{ dados.usuario.saldo_inicial }}" style="width:70px; border-radius:4px; border:1px solid var(--border-color); text-align:center;">
                        <button type="submit" style="font-size:0.7rem; background: var(--accent-terracotta); border:none; color:white; padding:2px 5px; border-radius:4px;">ok</button>
                    </form>
                </div>

                {% set total_entradas = dados.financeiro | selectattr('tipo', 'equalto', 'entradas') | map(attribute='valor') | sum %}
                {% set total_fixos = dados.financeiro | selectattr('tipo', 'equalto', 'gastos_fixos') | map(attribute='valor') | sum %}
                {% set total_variaveis = dados.financeiro | selectattr('tipo', 'equalto', 'gastos_variaveis') | map(attribute='valor') | sum %}
                {% set saldo_final = dados.usuario.saldo_inicial + total_entradas - (total_fixos + total_variaveis) %}

                <div class="resumo-row"><span>Total Entradas:</span><span style="color:var(--accent-green);">R$ {{ "%.2f"|format(total_entradas) }}</span></div>
                <div class="resumo-row"><span>Gastos Fixos:</span><span style="color:var(--accent-red);">R$ {{ "%.2f"|format(total_fixos) }}</span></div>
                <div class="resumo-row"><span>Gastos Variáveis:</span><span style="color:var(--accent-red);">R$ {{ "%.2f"|format(total_variaveis) }}</span></div>

                {% if saldo_final >= 0 %}
                <div class="saldo-final-box saldo-positivo">Sobra: R$ {{ "%.2f"|format(saldo_final) }} 🎉</div>
                {% else %}
                <div class="saldo-final-box saldo-negativo">Falta: R$ {{ "%.2f"|format(saldo_final) }} ⚠️</div>
                {% endif %}
            </div>

            <!-- Adicionar Lançamento -->
            <div class="fin-column">
                <h2 class="fin-title">💸 Lançar Transação</h2>
                <form action="/add_financeiro" method="POST" class="fin-form">
                    <input type="text" name="desc" placeholder="Descrição..." required>
                    <input type="number" step="0.01" name="valor" placeholder="Valor (R$)" required>
                    <select name="tipo" required>
                        <option value="entradas">Entrada (Salário, VR...) 📥</option>
                        <option value="gastos_fixos">Gasto Fixo (Contas) 🏠</option>
                        <option value="gastos_variaveis">Gasto Variável (Cartão...) 🛒</option>
                    </select>
                    <button type="submit">Salvar Registro</button>
                </form>

                <div class="fin-list">
                    {% for item in dados.financeiro %}
                    <div class="fin-item">
                        <span>
                            {% if item.tipo == 'entradas' %}📥{% elif item.tipo == 'gastos_fixos' %}🏠{% else %}🛒{% endif %}
                            {{ item.descricao }}
                        </span>
                        <span style="font-weight:bold; {% if item.tipo == 'entradas' %}color:var(--accent-green);{% else %}color:var(--text-main);{% endif %}">
                            R$ {{ "%.2f"|format(item.valor) }}
                            <a href="/delete_financeiro/{{ item.id }}" style="text-decoration:none; margin-left:8px;">🗑️</a>
                        </span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Quero vs Preciso -->
            <div class="filtro-impulso">
                <div class="filtro-box">
                    <h3 style="color:var(--accent-terracotta)">🛍️ Quero (Desejo)</h3>
                    <form action="/add_impulso/quero" method="POST">
                        <input type="text" name="item" placeholder="Blusinha, fone..." required>
                        <button type="submit">+</button>
                    </form>
                    <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                        {% for item in dados.desejos if item.tipo == 'quero' %}
                        <li style="margin-bottom:5px;">{{ item.item }} <a href="/delete_impulso/{{ item.id }}">🗑️</a></li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="filtro-box">
                    <h3 style="color:var(--accent-green)">📍 Preciso (Necessidade)</h3>
                    <form action="/add_impulso/preciso" method="POST">
                        <input type="text" name="item" placeholder="Lente do óculos, mercado..." required>
                        <button type="submit">+</button>
                    </form>
                    <ul style="padding-left:15px; margin:0; font-size:0.85rem;">
                        {% for item in dados.desejos if item.tipo == 'preciso' %}
                        <li style="margin-bottom:5px;">{{ item.item }} <a href="/delete_impulso/{{ item.id }}">🗑️</a></li>
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
    conn = obter_conexao()
    
    # Busca dados do usuário logado
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    
    # Busca tarefas do usuário
    tarefas_db = conn.execute('SELECT * FROM tarefas WHERE user_id = ?', (user_id,)).fetchall()
    brain_dump = [t for t in tarefas_db if t['coluna'] == 'brain_dump']
    foco_hoje = [t for t in tarefas_db if t['coluna'] == 'foco_hoje']
    concluido = [t for t in tarefas_db if t['coluna'] == 'concluido']
    
    # Busca metas SMART
    metas_smart = conn.execute('SELECT * FROM metas_smart WHERE user_id = ?', (user_id,)).fetchall()
    
    # Busca mídias
    midias = conn.execute('SELECT * FROM mídias WHERE user_id = ?', (user_id,)).fetchall()
    
    # Busca financeiro
    financeiro = conn.execute('SELECT * FROM financeiro WHERE user_id = ?', (user_id,)).fetchall()
    
    # Busca desejos (Quero vs Preciso)
    desejos = conn.execute('SELECT * FROM desejos WHERE user_id = ?', (user_id,)).fetchall()
    
    conn.close()
    
    dados = {
        "usuario": usuario,
        "brain_dump": brain_dump,
        "foco_hoje": foco_hoje,
        "concluido": concluido,
        "metas_smart": metas_smart,
        "midias": midias,
        "financeiro": financeiro,
        "desejos": desejos,
        "meta_livros_quero": usuario['meta_livros'],
        "meta_filmes_quero": usuario['meta_filmes']
    }
    
    return render_template_string(HTML_TEMPLATE, dados=dados)

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
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index', error='auth'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username').strip().lower()
    password = request.form.get('password')
    
    conn = obter_conexao()
    # Verifica se já existe
    existente = conn.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
    if existente:
        conn.close()
        return redirect(url_for('index', register=True, error='exists'))
    
    # Cria novo usuário
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, hash_senha(password)))
    conn.commit()
    
    # Faz login automático
    user_id = cursor.lastrowid
    conn.close()
    
    session['user_id'] = user_id
    session['username'] = username
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
        INSERT INTO metas_smart (user_id, goal_name, step1_desc, step1_time, step1_deadline)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], request.form.get("goal_name"), request.form.get("step1_desc"), request.form.get("step1_time"), request.form.get("step1_deadline")))
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
    conn = obter_conexao()
    conn.execute('''
        INSERT INTO financeiro (user_id, descricao, valor, tipo)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], request.form.get("desc"), float(request.form.get("valor")), request.form.get("tipo")))
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
    if saldo:
        conn = obter_conexao()
        conn.execute('UPDATE usuarios SET saldo_inicial = ? WHERE id = ?', (float(saldo), session['user_id']))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/add_impulso/<tipo>', methods=['POST'])
def add_impulso(tipo):
    if 'user_id' not in session: return redirect(url_for('index'))
    item = request.form.get("item")
    if item and tipo in ['quero', 'preciso']:
        conn = obter_conexao()
        conn.execute('INSERT INTO desejos (user_id, item, tipo) VALUES (?, ?, ?)', (session['user_id'], item, tipo))
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
    app.run(debug=True, host='0.0.0.0', port=5000)

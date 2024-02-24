from typing import Final
from tabulate import tabulate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pandas as pd
import pygsheets

TOKEN : Final = '7114531591:AAE9K7-80Gx-_sr_cfR1GuVupnAW5AFOO5o'
BOT_USERNAME : Final = '@MBE_Visagio_Bot'
PLACAR : Final = pd.DataFrame({'Dupla':[], 'Integrantes': [], 'Placar': [], 'ValorDiario': [], 'Meetup': [], 'Vibe': [], 'AtivFisica': [], 'AtivRelax': [], 'Atividade1': []})
GC : Final = pygsheets.authorize(service_file='credentials.json')
SH : Final = GC.open('MBE')
WKS : Final = SH[0]
ADMIN : Final = 6837505886

# Commands
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN
    if update.message.from_user.id == ADMIN:
        reset()
        await update.message.reply_text('Tabela resetada com sucesso')

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN
    if update.message.from_user.id == ADMIN:
        update_placar(context.args[0], context.args[1], context.args[2])
        await update.message.reply_text('Placar atualizado com sucesso')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WKS
    global PLACAR
    global ADMIN
    if update.message.from_user.id == ADMIN:
        WKS.set_dataframe(PLACAR,(1,1))
        await update.message.reply_text('Google sheets atualizado com sucesso')

# Handle Responses
def reset():
    global PLACAR
    PLACAR['ValorDiario'] = 0
    PLACAR['Meetup'] = False
    PLACAR['Vibe'] = False
    PLACAR['AtivFisica'] = 0
    PLACAR['AtivRelax'] = 0
    PLACAR['Atividade1'] = 0
    return 'Tabela Resetada com Sucesso'
    
def update_placar(nomeDupla, valor, coluna):
    global PLACAR
    idx = PLACAR.Dupla.explode().eq(nomeDupla).loc[lambda x: x].index.values[0]
    PLACAR.at[idx, coluna] = valor

def pontuar(idPessoal, pontos, typ):
    global PLACAR
    idx = PLACAR.Integrantes.explode().eq(idPessoal).loc[lambda x: x].index
    al = PLACAR.loc[idx]
    if al.empty:
        return f'Usuário não registrado em nenhuma dupla'
    al = al.iloc[0]
    if PLACAR.at[idx.values[0], "ValorDiario"] == 6:
        return f'Pontuação máxima diária já atingida'
    mini = min(6 - PLACAR.at[idx.values[0], "ValorDiario"], pontos)

    if typ == 'Meetup':
        if al['Meetup'] == True:
            return f'Atividade Meetup já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Meetup"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        return f'Atividade Meetup registrada com sucesso para a dupla "{al["Dupla"]}"'
    elif typ == 'Vibe':   
        if al['Vibe'] == True:
            return f'Atividade Vibe já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Vibe"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        return f'Atividade Vibe registrada com sucesso para a dupla "{al["Dupla"]}"'
    elif typ == 'Atividade1':   
        if al['Atividade1'] == True:
            return f'A atividade1 já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "Atividade1"] = True
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        return f'Atividade1 registrada com sucesso para a dupla "{al["Dupla"]}"'    
    elif typ == 'AtivFisica':
        if al['AtivFisica'] == sum(PLACAR.at[idx.values[0], "Integrantes"]):
            return f'A atividade física já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        if al['AtivFisica'] == idPessoal:
            return f'A atividade física já foi registrada por você para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "AtivFisica"] += idPessoal
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        return f'A atividade física registrada com sucesso para a dupla "{al["Dupla"]}"'
    elif typ == 'AtivRelax':
        if al['AtivRelax'] == sum(PLACAR.at[idx.values[0], "Integrantes"]):
            return f'A atividade relax já foi registrada anteriormente para a dupla "{al["Dupla"]}"'
        if al['AtivRelax'] == idPessoal:
            return f'A atividade relax já foi registrada por você para a dupla "{al["Dupla"]}"'
        PLACAR.at[idx.values[0], "AtivRelax"] += idPessoal
        PLACAR.at[idx.values[0], "Placar"] += mini
        PLACAR.at[idx.values[0], "ValorDiario"] += mini
        return f'A atividade relax registrada com sucesso para a dupla "{al["Dupla"]}"'
        
        

def handle_response(text: str, update: Update) -> str:
    processed: str = text.lower()
    global PLACAR
    idPessoal = update.message.from_user.id

    if '/registrar' == processed:
        return 'Necessário inserção do nome da dupla'
    
    if '/registrar' in processed:
        nomedupla = processed.split('/registrar')[1].strip()
        al = PLACAR.loc[PLACAR.Integrantes.explode().eq(idPessoal).loc[lambda x: x].index, "Dupla"]
        if not al.empty:
            return f'Usuário já registrado na dupla "{al.iloc[0]}"'
        
        if nomedupla not in PLACAR.Dupla.values:
            PLACAR = pd.concat([PLACAR, pd.DataFrame({'Dupla': [nomedupla], 'Integrantes': [{idPessoal}], 'Placar': [0], 'ValorDiario': [0], 'Meetup': [False], 'Vibe': [False], 'AtivFisica': [0], 'AtivRelax': [0], 'Atividade1': [False]})], axis=0, ignore_index=True)
            return 'Dupla Registrada com sucesso'
        else:
            row = PLACAR[PLACAR['Dupla'] == nomedupla].iloc[0]
            if len(row.Integrantes) == 2:
                return f'A dupla "{nomedupla}" já está cheia'
            else:
                PLACAR.loc[row.name, 'Integrantes'].add(idPessoal)
                return f'A dupla "{nomedupla}" foi completada com sucesso'
       
    
    if '/atividade1' == processed:
        if update.message.photo == ():
            return 'Atividade sem imagem não será registrada'
        return pontuar(idPessoal, 4, 'Atividade1')

    if '/placar' == processed:
        p = PLACAR[["Dupla", "Placar"]]
        p["Placar"] = p["Placar"].astype('int')
        m = p.Dupla.str.len().max()
        p.Dupla = p.Dupla.str.ljust(m, ' ')
        p = p.to_string(index = False)

        return f"```{p}```"
        
    
    if '/meetup' == processed:
        if update.message.photo == ():
           return 'Atividade sem imagem não será registrada'
        return pontuar(idPessoal, 4, 'Meetup')

    if '/ativfisica' == processed:
        if update.message.photo == ():
            return 'Atividade sem imagem não será registrada'
        return pontuar(idPessoal, 1, 'AtivFisica')
    
    if '/ativrelax' == processed:
        if update.message.photo == ():
            return 'Atividade sem imagem não será registrada'
        return pontuar(idPessoal, 1, 'AtivRelax')
    
    if '/vibe' == processed:
        if update.message.photo == ():
            return 'Atividade sem imagem não será registrada'
        return pontuar(idPessoal, 4, 'Vibe')
    
    return 'Comando não reconhecido'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    if update.message.text != None:
        text: str = update.message.text
    else:
        text: str = update.message.caption
    if text[0] == '/' and message_type == 'group':
        print(f'User {update.message.from_user.id} in {message_type}: {text}')
        response: str = handle_response(text, update)
    
        print('Bot: ', response)
        if response != '':
            await update.message.reply_text(response, parse_mode="Markdown")
    

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('reset', reset_command))
    app.add_handler(CommandHandler('update', update_command))
    app.add_handler(CommandHandler('custom', custom_command))


    app.add_handler(MessageHandler(filters.ALL, handle_message))


    app.add_error_handler(error)
    print('Polling...')
    app.run_polling(poll_interval=3)
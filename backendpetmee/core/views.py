# Padrão recomendado pela comunidade Django:


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from backendpetmee.supabase_client import supabase
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Pet
from supabase import create_client, Client

def cadastro_user(request):
    if request.method == 'POST':
        nome_completo = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '').strip()

        if not nome_completo or not email or not senha:
            messages.error(request, "Por favor, preencha todos os campos.")
            return render(request, 'registro/registro.html')

        try:
            auth_response = supabase.auth.sign_up(
                credentials={
                    'email': email,
                    'password': senha,
                    'options': {
                        'data': {
                            'nome_completo': nome_completo,
                        }
                    }
                }
            )

            user = auth_response.user
            if not user:
                messages.error(request, "Não foi possível criar a conta. Verifique os dados.")
                return render(request, 'registro/registro.html')

            try:
                supabase.table("Usuarios").insert({
                    "id": str(user.id),
                    "nome_completo": nome_completo,
                }).execute()
            except Exception as db_err:
                print(f'[AVISO] Conta criada no Auth, mas falhou insert em Usuarios: {db_err}')

            messages.success(request, "Cadastro realizado com sucesso! Faça seu login.")
            return redirect('login')

        except Exception as e:
            print(f'[ERRO NO CADASTRO]: {e}')
            messages.error(request, f"Erro ao cadastrar: {str(e)}")

    return render(request, 'registro/registro.html')


def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '').strip()

        try:
            resposta = supabase.auth.sign_in_with_password({
                'email': email,
                'password':senha,
            })

            if resposta.user:
                request.session['user_id'] = resposta.user.id
                return redirect('home') 

        except Exception as e:
            messages.error(request, "E-mail ou senha inválidos.")
            return redirect('login')
    return render(request, 'Login/Login.html')

def home(request):
    if 'user_id' not in request.session:
        return redirect('login')

    return render(request, 'home/inicio.html')

def detalhes_pet(request, pet_id):
    response = supabase.table('Pet').select('*').eq('pet_id', pet_id).execute()
    pet = response.data[0] if response.data else None
    context = {
        'pet':pet
    }
    return render(request, 'perfil1.html', context)
    

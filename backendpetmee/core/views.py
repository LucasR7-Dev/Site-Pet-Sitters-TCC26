from uuid import UUID

from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from backendpetmee.supabase_client import supabase, SUPABASE_ANON_KEY, SUPABASE_URL
from supabase import create_client


def _user_id(request):
    value = request.session.get('user_id')
    try:
        return str(UUID(str(value))) if value else None
    except (TypeError, ValueError):
        return None


def _client(request):
    """Cliente por requisição: evita compartilhar a sessão de um usuário entre usuários."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    access_token = request.session.get('supabase_access_token')
    refresh_token = request.session.get('supabase_refresh_token')
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass
    return client


def _select_one(request, table, column, value):
    response = _client(request).table(table).select('*').eq(column, value).limit(1).execute()
    return response.data[0] if response.data else None


def _ensure_profile(request, user_id):
    """Cria o perfil para contas existentes antes da nova tabela de perfis."""
    try:
        perfil = _select_one(request, 'usuarios', 'id', user_id)
    except Exception:
        # A tela inicial continua utilizável mesmo em uma falha transitória do REST.
        return None
    if perfil:
        return perfil
    try:
        user = _client(request).auth.get_user().user
        metadata = user.user_metadata or {}
        nome = metadata.get('nome_completo') or user.email.split('@')[0]
        _client(request).table('usuarios').insert({'id': user_id, 'nome_completo': nome}).execute()
        return _select_one(request, 'usuarios', 'id', user_id)
    except Exception:
        return None


def cadastro_user(request):
    if request.method == 'POST':
        nome_completo = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '')
        if not nome_completo or not email or not senha:
            messages.error(request, 'Preencha todos os campos.')
            return render(request, 'registro/registro.html')
        try:
            resposta = supabase.auth.sign_up({
                'email': email, 'password': senha,
                'options': {'data': {'nome_completo': nome_completo}},
            })
            if not resposta.user:
                raise ValueError('Usuário não retornado pelo Supabase.')
            # Em projetos com confirmação de e-mail, o usuário ainda não tem sessão
            # autenticada aqui. O trigger do schema cria o perfil nesse caso.
            try:
                supabase.table('usuarios').upsert({
                    'id': str(resposta.user.id), 'nome_completo': nome_completo,
                }).execute()
            except Exception:
                pass
            messages.success(request, 'Cadastro realizado. Faça seu login.')
            return redirect('login')
        except Exception:
            messages.error(request, 'Não foi possível concluir o cadastro. Tente novamente.')
    return render(request, 'registro/registro.html')


def login_user(request):
    if request.method == 'POST':
        try:
            resposta = supabase.auth.sign_in_with_password({
                'email': request.POST.get('email', '').strip(),
                'password': request.POST.get('password', ''),
            })
            if resposta.user:
                request.session['user_id'] = str(resposta.user.id)
                request.session['supabase_access_token'] = resposta.session.access_token
                request.session['supabase_refresh_token'] = resposta.session.refresh_token
                return redirect('home')
        except Exception:
            pass
        messages.error(request, 'E-mail ou senha inválidos.')
        return redirect('login')
    return render(request, 'Login/Login.html')


def home(request):
    user_id = _user_id(request)
    if not user_id:
        return redirect('login')
    _ensure_profile(request, user_id)
    try:
        client = _client(request)
        pets = client.table('pets').select('*').eq('disponivel', True).order('created_at', desc=True).execute().data
        # Enquanto não há um campo de papel/role, todo perfil cadastrado pode
        # aparecer como cuidador. Isso também permite visualizar o primeiro card.
        cuidadores = client.table('usuarios').select('*').order('created_at', desc=True).limit(6).execute().data
    except Exception:
        pets, cuidadores = [], []
    return render(request, 'home/inicio.html', {'pets': pets, 'cuidadores': cuidadores})


def cadastrar_pet(request):
    owner_id = _user_id(request)
    if not owner_id:
        return redirect('login')
    if request.method == 'POST':
        fields = ('nome', 'especie', 'raca', 'sexo', 'porte', 'idade', 'localizacao', 'saude', 'sobre', 'foto_url')
        pet = {field: request.POST.get(field, '').strip() for field in fields}
        if not pet['nome'] or not pet['especie'] or not pet['localizacao']:
            messages.error(request, 'Nome, espécie e localização são obrigatórios.')
        else:
            pet.update({'tutor_id': owner_id, 'disponivel': True})
            try:
                novo_pet = _client(request).table('pets').insert(pet).execute().data[0]
                messages.success(request, 'Pet cadastrado com sucesso.')
                return redirect('detalhes_pet', pet_id=novo_pet['id'])
            except Exception:
                messages.error(request, 'Não foi possível salvar o pet. Confira o SQL do Supabase.')
    return render(request, 'pets/formulario.html')


def detalhes_pet(request, pet_id):
    try:
        pet = _select_one(request, 'pets', 'id', pet_id)
    except Exception as exc:
        raise Http404('Pet não encontrado.') from exc
    if not pet:
        raise Http404('Pet não encontrado.')
    return render(request, 'perfil/perfil1.html', {
        'pet': pet, 'is_owner': _user_id(request) == str(pet.get('tutor_id')),
    })


def meu_perfil(request):
    user_id = _user_id(request)
    return redirect('login') if not user_id else redirect('perfil_usuario', user_id=user_id)


def perfil_usuario(request, user_id):
    try:
        perfil = _select_one(request, 'usuarios', 'id', str(user_id))
        if not perfil and _user_id(request) == str(user_id):
            perfil = _ensure_profile(request, str(user_id))
        avaliacoes = _client(request).table('avaliacoes').select('*').eq('avaliado_id', str(user_id)).order('created_at', desc=True).execute().data
    except Exception:
        perfil, avaliacoes = None, []
    if not perfil:
        raise Http404('Perfil não encontrado.')
    media = round(sum(item['nota'] for item in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None
    return render(request, 'perfil/perfil.html', {
        'perfil': perfil, 'avaliacoes': avaliacoes, 'media_avaliacoes': media,
        'is_owner': _user_id(request) == str(user_id),
    })


def editar_perfil(request, user_id):
    if _user_id(request) != str(user_id):
        return HttpResponseForbidden('Você só pode editar o seu próprio perfil.')
    if request.method == 'POST':
        values = {key: request.POST.get(key, '').strip() for key in ('nome_completo', 'cidade', 'estado', 'idade', 'bio', 'avatar_url')}
        try:
            _client(request).table('usuarios').update(values).eq('id', str(user_id)).execute()
            messages.success(request, 'Perfil atualizado.')
            return redirect('perfil_usuario', user_id=user_id)
        except Exception:
            messages.error(request, 'Não foi possível atualizar o perfil.')
    return render(request, 'perfil/editar.html', {'perfil': _select_one(request, 'usuarios', 'id', str(user_id))})


def criar_avaliacao(request, user_id):
    autor_id = _user_id(request)
    if not autor_id:
        return redirect('login')
    if autor_id == str(user_id):
        messages.error(request, 'Você não pode avaliar o próprio perfil.')
    elif request.method == 'POST':
        try:
            nota = int(request.POST.get('nota', 0))
            comentario = request.POST.get('comentario', '').strip()
            if nota not in range(1, 6) or not comentario:
                raise ValueError
            _client(request).table('avaliacoes').upsert({
                'autor_id': autor_id, 'avaliado_id': str(user_id), 'nota': nota, 'comentario': comentario,
            }, on_conflict='autor_id,avaliado_id').execute()
            messages.success(request, 'Sua avaliação foi publicada.')
        except ValueError:
            messages.error(request, 'Informe uma nota de 1 a 5 e escreva um comentário.')
        except Exception:
            messages.error(request, 'Não foi possível publicar sua avaliação.')
    return redirect('perfil_usuario', user_id=user_id)

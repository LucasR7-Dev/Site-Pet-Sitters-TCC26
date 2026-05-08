//Api do IBGE para carregar os estados e cidades do Brasil pode ser usada para criar um filtro de busca por localização em outras paginas do site, como a página de busca de cuidadores. O código abaixo é um exemplo de como usar a API do IBGE para carregar os estados e cidades em um formulário de busca:

const selectEstado = document.getElementById('estado');
const selectCidade = document.getElementById('cidade');
//Função para carregar os Estados e abrir a pagina
async function carregarEstado(){
const response = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome')
const estados = await response.json();

estados.forEach(estado => {
    const option = document.createElement('option');
    option.value = estado.sigla;
    option.textContent = estado.nome;
    selectEstado.appendChild(option)
});
}
//Função para carregar acidades quando o estado mudar
selectEstado.addEventListener('change', async() =>{
    const sigla = selectEstado.value;
    selectCidade.innerHTML = '<option value="">Carregando...</option>';

    if (!sigla){
        selectCidade.innerHTML = '<option value""">Selecione o Estado primeiro</option>'
        return;
    }
    const response = await fetch(`https://servicodados.ibge.gov.br/api/v1/localidades/estados/${sigla}/municipios`)
    const cidades = await response.json();

    selectCidade.innerHTML = '<option value="">Selecione a cidade</option>';
    cidades.forEach(cidade => {
        const option = document.createElement('option');
        option.value = cidade.nome;
        option.textContent = cidade.nome;
        selectCidade.appendChild(option);
})
});
carregarEstado();
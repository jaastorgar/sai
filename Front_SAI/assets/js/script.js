document.addEventListener('DOMContentLoaded', function () {
    // Menu toggle para móvil
    const menuToggle = document.querySelector('.menu-toggle');
    const menu = document.querySelector('.menu');

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            menu.classList.toggle('show');
        });
    }

    // Cerrar menú cuando se redimensiona la pantalla
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 769) {
            menu.classList.remove('show');
        }
    });

    // Tab switching para Misión/Visión/Valores
    const listaItems = document.querySelectorAll('.lista-item');
    const contenidos = document.querySelectorAll('.contenido');

    function mostrarContenido(index) {
        contenidos.forEach(contenido => contenido.classList.remove('show'));
        const contenidoClase = ['mision', 'vision', 'valor'][index];
        const contenidoEl = document.querySelector(`.${contenidoClase}`);
        if (contenidoEl) {
            contenidoEl.classList.add('show');
        }
    }

    function actualizarEstilosLista() {
        listaItems.forEach(item => {
            item.classList.remove('active');
        });
    }

    listaItems.forEach((item, index) => {
        item.addEventListener('click', () => {
            actualizarEstilosLista();
            item.classList.add('active');
            mostrarContenido(index);
        });
    });

    // Activar primer item por defecto
    if (listaItems.length > 0) {
        listaItems[0].classList.add('active');
        mostrarContenido(0);
    }
});



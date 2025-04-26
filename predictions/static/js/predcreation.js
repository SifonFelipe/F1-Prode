document.addEventListener('DOMContentLoaded', function() {
    // En lugar de definir los datos de los pilotos en JavaScript,
    // ahora los recibimos generados por Django
    
    const selections = {};
    
    // Hacer que cada tarjeta de piloto sea arrastrable
    document.querySelectorAll('.driver-card').forEach(card => {
        // Evento de arrastre
        card.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('driverId', this.dataset.driverId);
        });
        
        // Nuevo: Evento de clic para colocar automáticamente
        card.addEventListener('click', function() {
            const driverId = this.dataset.driverId;
            
            // Verificar si el piloto ya está seleccionado
            if (Object.values(selections).includes(driverId)) {
                alert(`${this.querySelector('.name').textContent} ya está seleccionado`);
                return;
            }
            
            // Encontrar la primera posición disponible
            const allPositions = document.querySelectorAll('.position-slot');
            let firstAvailablePosition = null;
            
            for (const posSlot of allPositions) {
                const position = posSlot.dataset.position;
                if (!selections[position]) {
                    firstAvailablePosition = position;
                    break;
                }
            }
            
            if (firstAvailablePosition) {
                // Obtener los datos del piloto
                const driverName = this.querySelector('.name').textContent;
                const driverTeam = this.querySelector('.team').textContent;
                const driverImg = this.querySelector('img').src;
                
                // Colocar el piloto en la posición
                placeDriverInPosition({
                    id: driverId,
                    name: driverName,
                    team: driverTeam,
                    img: driverImg
                }, firstAvailablePosition);
                
                // Resaltar brevemente la posición para destacar dónde se colocó
                const positionSlot = document.querySelector(`.position-slot[data-position="${firstAvailablePosition}"]`);
                positionSlot.classList.add('highlight-placement');
                setTimeout(() => {
                    positionSlot.classList.remove('highlight-placement');
                }, 800);
                
                // Actualizar visualización
                updateDriversPool();
            } else {
                alert('No hay posiciones disponibles. Elimina algún piloto antes de agregar uno nuevo.');
            }
        });
    });
    
    // Configurar los eventos de arrastrar y soltar para las posiciones
    document.querySelectorAll('.position-slot').forEach(slot => {
        slot.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('active');
        });
        
        slot.addEventListener('dragleave', function() {
            this.classList.remove('active');
        });
        
        slot.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('active');
            
            const driverId = e.dataTransfer.getData('driverId');
            const driverCard = document.querySelector(`.driver-card[data-driver-id="${driverId}"]`);
            
            if (driverCard) {
                // Verificar si el piloto ya está seleccionado en otra posición
                for (const pos in selections) {
                    if (selections[pos] == driverId) {
                        alert(`${driverCard.querySelector('.name').textContent} ya está seleccionado en la posición ${pos}`);
                        return;
                    }
                }
                
                const position = this.dataset.position;
                
                // Clonar la información del piloto
                const driverName = driverCard.querySelector('.name').textContent;
                const driverTeam = driverCard.querySelector('.team').textContent;
                const driverImg = driverCard.querySelector('img').src;
                
                // Colocar el piloto en la posición
                placeDriverInPosition({
                    id: driverId,
                    name: driverName,
                    team: driverTeam,
                    img: driverImg
                }, position);
                
                // Actualizar visualización
                updateDriversPool();
            }
        });
    });
    
    // Función para colocar un piloto en una posición
    function placeDriverInPosition(driver, position) {
        const positionSlot = document.querySelector(`.position-slot[data-position="${position}"]`);
        const positionSlotContent = positionSlot.querySelector('.position-slot-content');
        
        // Limpiar el contenido actual
        positionSlotContent.innerHTML = '';
        
        // Crear el elemento del piloto seleccionado
        const selectedDriver = document.createElement('div');
        selectedDriver.className = 'selected-driver';
        
        // Cambiar la imagen si es la primera posición
        let driverImgSrc = driver.img; // Imagen por defecto
        if (position === '1') {
            driverImgSrc = `/static/img/win-images/${driver.name.toLowerCase()}-win.png`; // Cambiar a la imagen ganadora
        }
        
        const driverImg = document.createElement('img');
        driverImg.src = driverImgSrc;
        driverImg.alt = driver.name;
        
        const driverInfo = document.createElement('div');
        driverInfo.className = 'driver-info';
        driverInfo.innerHTML = `
            <div class="name">${driver.name}</div>
            <div class="team">${driver.team}</div>
        `;
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-driver';
        removeBtn.innerHTML = '&times;';
        removeBtn.addEventListener('click', function() {
            delete selections[position];
            
            // Restaurar el mensaje vacío
            positionSlotContent.innerHTML = '';
            const emptySlotMsg = document.createElement('div');
            emptySlotMsg.className = 'empty-slot-msg';
            emptySlotMsg.textContent = 'Arrastra un piloto aquí';
            positionSlotContent.appendChild(emptySlotMsg);
            
            positionSlot.classList.remove('filled');
            
            // Actualizar visualización
            updateDriversPool();
        });
        
        selectedDriver.appendChild(driverImg);
        selectedDriver.appendChild(driverInfo);
        selectedDriver.appendChild(removeBtn);
        
        positionSlotContent.appendChild(selectedDriver);
        positionSlot.classList.add('filled');
        
        // Guardar la selección
        selections[position] = driver.id;
    }

    // Actualizar el pool de pilotos disponibles
    function updateDriversPool() {
        const selectedDriverIds = Object.values(selections);
        
        // Ocultar los pilotos seleccionados
        document.querySelectorAll('.driver-card').forEach(card => {
            if (selectedDriverIds.includes(card.dataset.driverId)) {
                card.style.display = 'none';
            } else {
                card.style.display = 'flex';
            }
        });
    }

    // Botón para reiniciar el pronóstico
    document.getElementById('resetBtn').addEventListener('click', function() {
        if (confirm('¿Estás seguro de querer reiniciar tu pronóstico?')) {
            // Limpiar todas las selecciones
            for (const position in selections) {
                delete selections[position];
            }
            
            // Limpiar todas las posiciones
            const positionSlots = document.querySelectorAll('.position-slot');
            positionSlots.forEach(slot => {
                const positionSlotContent = slot.querySelector('.position-slot-content');
                
                positionSlotContent.innerHTML = '';
                const emptySlotMsg = document.createElement('div');
                emptySlotMsg.className = 'empty-slot-msg';
                emptySlotMsg.textContent = 'Arrastra un piloto aquí';
                positionSlotContent.appendChild(emptySlotMsg);
                
                slot.classList.remove('filled');
            });
            
            // Actualizar visualización
            updateDriversPool();
        }
    });

    // Botón para guardar el pronóstico
    document.getElementById('saveBtn').addEventListener('click', function() {
        const totalPositions = Object.keys(selections).length;
        const positions = document.querySelectorAll('.position-slot').length;
        
        if (totalPositions < positions) {
            alert(`¡Faltan posiciones por completar! Has seleccionado ${totalPositions} de ${positions} pilotos.`);
            return;
        }
        
        // Preparar los datos para enviar al servidor
        const predictionData = {
            race_id: document.getElementById('race-data').dataset.raceId,
            positions: selections,
        };
        
        // Obtener el token CSRF de forma adecuada
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Enviar datos al servidor mediante fetch
        fetch(document.getElementById('prediction-form').dataset.saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(predictionData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('¡Pronóstico guardado con éxito!');
            } else {
                alert('Error al guardar el pronóstico: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar el pronóstico. Por favor, intenta nuevamente.');
        });
    });

    // Simulación de temporizador de cuenta regresiva
    function updateCountdown() {
        const countdownEl = document.getElementById('countdown');

        if (countdownEl.textContent == "out") {
            countdownEl.textContent = "¡Tiempo finalizado!";
            countdownEl.style.color = "var(--f1-red)";
            const actionsDiv = document.querySelector(`.actions`);
            // Limpiar el contenido actual
            actionsDiv.innerHTML = '';
            return;
        }
        
        let [hours, minutes, seconds] = countdownEl.textContent.split(':').map(Number);
        
        seconds--;
        
        if (seconds < 0) {
            seconds = 59;
            minutes--;
            
            if (minutes < 0) {
                minutes = 59;
                hours--;
                
                if (hours < 0) {
                    countdownEl.textContent = "¡Tiempo finalizado!";
                    alert("¡El tiempo ha terminado!");
                    countdownEl.style.color = "var(--f1-red)";
                    const actionsDiv = document.querySelector(`.actions`);
                    // Limpiar el contenido actual
                    actionsDiv.innerHTML = '';
                    return;
                }
            }
        }
        
        countdownEl.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        setTimeout(updateCountdown, 1000);
    }

    // Inicializar
    updateDriversPool();
    updateCountdown();
});

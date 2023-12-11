## Протокол файлового сервера
* Клиенты файлового сервера устанавливают TCP-соединения с сервером и отправляют текстовые сообщения (команды).
* Каждая команда представлена набором латинских символов. Команда так же может состять из тела команды.  
* В зависимости от команды сервер отсылает пользователю информационное сообщение о статусе выполнения
* Если команда не известна серверу, он высылает в ответ ошибку с сообщением: `no such command`.
  
Для организации связи реализовано два протокола SimpleProto и TCD8. При подключении пользователя сервер отправляет [запрос "id?"](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L10) для получения id пользователя

### SimpleProto
Данный протокол отправялет данные "как есть" - без дополнительных полей. 
Отправка файлов на сервер данным протоколом не предусмотрена

### TCD8
Формат сообщений:
* клиент - отправка запроса [`BaseProtocol.send_request`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L117) : `_полная длина посылки [8 bytes]` + `длина команды [8 bytes]` + `длина данных для отправки [8 bytes]` + `команда` + `данные (если отправляем файл)`
* сервер - отправка ответа [`BaseProtocol.send_data`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L80): `полная длина посылки [8 bytes]` + `данные`

Данный протокол поддерживает отправку файлов на сервер, а также дозагрузку файлов, если во время отправки соеднинение было разорвано.
Процесс общения при отправки файла выглядит следующим образом:
* -> клиент отправляет запрос на отправку файла [`BaseProtocol.file_send_request`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L137): `полная длина посылки [8 bytes]` + `длина команды [8 bytes]` + `длина данных для отправки (=0) [8 bytes]` + `команда`
* -> сервер проверяет что в каталоге хранения файла нет его части (filename.extenstion.part) 
  <br/>Если нет - отправялем в ответ сообщение формата:  `полная длина посылки [8 bytes]` + `0 [8 bytes]`
  <br/>Если есть - отправялем в ответ сообщение формата:  `полная длина посылки [8 bytes]` + `размер сохраненной части файла в байтах`
* -> клиент получает ответ и отправляет файл целиком или его недостающую часть.


### Поддерживаемые команды
| Команда     | Тело команды                 | Тело ответа             | Ошибки        | Описание        |
|-------------|------------------------------|-------------------------|---------------|-----------------|
| [whoami](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L252)      | None                        |**id** = id пользователя<br/> **Restrictions** = словарь с установленными правами доступа<br/>**current path** = текущий каталог <br/>**home path** = домашний каталог<br/>**address** = (ip адрес, порт) | None| Информация о пользователе |
| [where](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L24)       	|None														|[>] you are now in "путь"						|None|Отображение пути текущего каталога|
| [list](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L53)    		|None или абсолютный путь или относительный путь			|[>] 'путь'<br/>folder> .. каталог<br/>> .. файл|*Если указан несуществующий каталог| Отображение списка папок и файлов|
| [jump](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L200)   		|None или абсолютный путь или относительный путь			|[>] path changed to 'путь' 				|*Если указан несуществующий каталог| Сменить текущий каталог|
| [info](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L226) 			|абсолютный путь или относительный путь каталога или файла |[>] 'путь': <br/> Size: ...<br/> Permissions: ...<br/> Owner: ...<br/> Created: ...<br/> Last modified: ...<br/> Last accessed: ...<br/> |*Если указан несуществующий каталог или файл| Отображение информации о файле или каталоге
| [nefo](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L77)   		|абсолютный путь или относительный путь каталога			|[>] successfully created folder 'путь'	|*Если указано недопустимое имя каталога| Создание нового каталога|
| [defo](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L100)    		|абсолютный путь или относительный путь каталога			|[>] successfully deleted folder 'путь'	|*Если указано недопустимое имя каталога<br/>*Если каталог не найден| Удаление каталога |
| [defi](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L121)    		|абсолютный путь или относительный путь файла				|[>] successfully deleted file 'путь до файла'|*Если файл не найден| Удаление файла |  
| [open](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L31)  		|абсолютный путь или относительный путь файла				|данные файла| None| Открыть файл |    
| [send](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L142)<br/>(только TCD8)|Путь до посылаемого файла + путь сохранения		|[>] file was successfully saved to "путь до файла" | None | Отправка файла|


### Расширенные команды
| Команда     | Тело команды                 | Тело ответа             | Ошибки        | Описание        |
|-------------|------------------------------|-------------------------|---------------|-----------------|
|[acts](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L10)| None| Active users: <br/>[number] ('ip' , 'порт') - имя пользователя <br/> Stored users: <br/> имя пользователя  <br/> ... | None | Отображение списка подключенных пользователей и сохраненных|
|[delr](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L98)|delr имя пользователя -[rwx] путь до каталога или файла | UserData(uid='имя пользователя', current_path='текущий каталог', restrictions={'w': ['...'], 'r': ['...'], 'x': ['...']}, home_path='домашний каталог') | *Если пользователь не найден | удаление запретов пользователя|  
|[setr](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L58)|setr имя пользователя -[rwx] путь до каталога или файла | UserData(uid='имя пользователя', current_path='текущий каталог', restrictions={'w': ['...'], 'r': ['...'], 'x': ['...']}, home_path='домашний каталог') |*Если пользователь не найден| добавление запретов пользователя|  
|[uinf](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L28)|имя пользователя| User 'имя' info:<br/> uid - имя<br/>current_path - 'текущий каталог'<br/>restrictions - словарь с правами доступа<br/>home_path - домашний каталог|*Если пользователь не найден|Вывод информации о пользователе|






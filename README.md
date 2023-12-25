## Протокол файлового сервера
* Клиенты файлового сервера устанавливают TCP-соединения с сервером и отправляют текстовые сообщения (команды).
* Каждая команда представлена набором латинских символов. Команда может состять из нескольких слов - данные слова пишутся через пробел.  
* В зависимости от команды сервер отсылает пользователю информационное сообщение о статусе выполнения
* Если команда не известна серверу, он высылает в ответ ошибку с сообщением: `no such command`.
  
Для организации связи реализовано два протокола SimpleProto и TCD8. При подключении пользователя сервер отправляет [запрос "id?"](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L11) для получения id пользователя
#### Настройки сервера
Настройки сервера хранятся в файле config.toml в каталоге ./cfg</br>
Структура файла:</br>
**[conn]**</br>
host = "" # _адрес сервера_ </br>
port = 3233 # _портсервера_ </br>
proto = "simple" # avaliable simple - SimpleProto , tcd8 - TCD8 # _используемый протокол_ </br>

**[saveloader]**</br>
type = 'json' # avaliable mongo, json # _способ хранения данных пользователей_ </br>
connection = {host  = '127.0.0.1', port = 27017, user = '', password = '', auth = false} # _строка подключения к MongoDB_ </br>
db = {database = 'fsdb', collection = 'fsusers'} # _настройка имен базы данных и коллекции в MongoDB _</br>
storage = 'storage' # _имя каталога с файловыми пространствами пользователей_ </br>




### SimpleProto
Данный протокол отправялет данные "как есть" - без дополнительных полей. Отправка заканчивается сообщением `\x04` 
Отправка файлов на сервер реалиована функцией [`BaseProtocol.SimpleProto.file_send_request`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L264)
Процесс отправки файла:
* отправка запроса `rawsend имя_файла количество_байт_для_отправки`
* отправка файла (см. пример реализации в функции rawsend)
Для отправки части файла необходимо указать количество байт для отправки большее, чем будет фактически послано. При этом файл сохранится как имя_файла.part.
Дозагрузка такого файла осущесвляется отправкой запроса `rawsend имя_файла количество_байт_для_отправки`. Отправленные байты будут дозаписаны в файл.
После завершения сервер прислает в ответ сообщение  - 'имя_файл was successfully saved to путь_до_файла\имя_файла'.
Файл сохраняется в тот каталог где находится пользователь (команда `where` отображает его)

### TCD8
Формат сообщений:
* клиент - отправка запроса [`BaseProtocol.send_request`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L132) : `_полная длина посылки [8 bytes]` + `длина команды [8 bytes]` + `длина данных для отправки [8 bytes]` + `команда` + `данные (если отправляем файл)`
* сервер - отправка ответа [`BaseProtocol.send_data`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L83): `полная длина посылки [8 bytes]` + `данные`

Данный протокол поддерживает отправку файлов на сервер, а также дозагрузку файлов, если во время отправки соеднинение было разорвано. При загрузке файлов используется стандартные функции [`BaseProtocol.send_data`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L83) и  [`BaseProtocol.receive_reply`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L139) с флагом with_ack.
Процесс общения при отправки файла выглядит следующим образом:
* -> клиент отправляет запрос на отправку файла [`BaseProtocl.file_send_request`](https://github.com/paparyadom/Rub/blob/master/Protocols/BaseProtocol.py#L165): `полная длина посылки [8 bytes]` + `длина команды [8 bytes]` + `длина данных для отправки (=0) [8 bytes]` + `команда`
* -> сервер проверяет разрешения на запись файла и что существует указанный путь сохранения файла. В случае если одно из условий не выполнено отправляет ответ с флагами with_ack=True, ack=False, а также причину в отказе операции. В случае если все условия выполнены сервер проверяет наличие недозагруженных частей файла:
  <br/>если нет - отправялем в ответ сообщение формата: отправялется ответ с флагами with_ack=True, ack=True `полная длина посылки [8 bytes]` + `флаг разрешения отправки [1 bytes]` + `0 [8 bytes]`
  <br/>Если есть - отправялем в ответ сообщение формата: отправялется ответ с флагами with_ack=True, ack=True `полная длина посылки [8 bytes]` + `флаг разрешения отправки [1 bytes]` + `размер сохраненной части файла в байтах`
* -> клиент получает ответ и отправляет файл целиком или его недостающую часть.


### Поддерживаемые команды
| Команда     | Тело команды                 | Тело ответа             | Ошибки        | Описание        |
|-------------|------------------------------|-------------------------|---------------|-----------------|
| [whoami](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L276)      | None                        |**id** = id пользователя<br/> **Restrictions** = словарь с установленными правами доступа<br/>**current path** = текущий каталог <br/>**home path** = домашний каталог<br/>**address** = (ip адрес, порт) | None| Информация о пользователе |
| [where](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L36)       	|None														|[>] you are now in "путь"						|None|Отображение пути текущего каталога|
| [list](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L65)    		|None или абсолютный путь или относительный путь			|[>] 'путь'<br/>folder> .. каталог<br/>> .. файл|*Если указан несуществующий каталог| Отображение списка папок и файлов|
| [jump](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L224)   		|None или абсолютный путь или относительный путь			|[>] path changed to 'путь' 				|*Если указан несуществующий каталог| Сменить текущий каталог|
| [info](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L250) 			|абсолютный путь или относительный путь каталога или файла |[>] 'путь': <br/> Size: ...<br/> Permissions: ...<br/> Owner: ...<br/> Created: ...<br/> Last modified: ...<br/> Last accessed: ...<br/> |*Если указан несуществующий каталог или файл| Отображение информации о файле или каталоге
| [nefo](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L89)   		|абсолютный путь или относительный путь каталога			|[>] successfully created folder 'путь'	|*Если указано недопустимое имя каталога| Создание нового каталога|
| [defo](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L112)    		|абсолютный путь или относительный путь каталога			|[>] successfully deleted folder 'путь'	|*Если указано недопустимое имя каталога<br/>*Если каталог не найден| Удаление каталога |
| [defi](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L133)    		|абсолютный путь или относительный путь файла				|[>] successfully deleted file 'путь до файла'|*Если файл не найден| Удаление файла |  
| [open](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L43)  		|абсолютный путь или относительный путь файла				|данные файла|*Если указан пустой путь до файла<br/>*Если указаного пути не существует | Открыть файл |    
| [send](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L154)<br/>(только TCD8)|Путь до посылаемого файла или имя файла '>' путь сохранения файла		|[>] file was successfully saved to "путь до файла" | *Если путь сохранения не существует<br/>*Если стоит запрет для пользователя на запись | Отправка файла|
| [rawsend](https://github.com/paparyadom/Rub/blob/master/Commands/UserCommands.py#L283)<br/>(только SimpleProto)|имя_файла количество_байт 		|[>] file was successfully saved to "путь до файла" | | Отправка файла|


### Расширенные команды
| Команда     | Тело команды                 | Тело ответа             | Ошибки        | Описание        |
|-------------|------------------------------|-------------------------|---------------|-----------------|
|[acts](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L9)| None| Active users: <br/>[number] ('ip' , 'порт') - имя пользователя <br/> Stored users: <br/> имя пользователя  <br/> ... | None | Отображение списка подключенных пользователей и сохраненных|
|[delp](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L101)|имя пользователя -[rwx] путь до каталога или файла | UserData(uid='имя пользователя', current_path='текущий каталог', restrictions={'w': ['...'], 'r': ['...'], 'x': ['...']}, home_path='домашний каталог') | *Если пользователь не найден | удаление запретов пользователя|  
|[setp](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L57)|имя пользователя -[rwx] путь до каталога или файла | UserData(uid='имя пользователя', current_path='текущий каталог', restrictions={'w': ['...'], 'r': ['...'], 'x': ['...']}, home_path='домашний каталог') |*Если пользователь не найден| добавление запретов пользователя|  
|[uinf](https://github.com/paparyadom/Rub/blob/master/Commands/SuperUserCommands.py#L27)|имя пользователя| User 'имя' info:<br/> uid - имя<br/>current_path - 'текущий каталог'<br/>restrictions - словарь с правами доступа<br/>home_path - домашний каталог|*Если пользователь не найден|Вывод информации о пользователе|






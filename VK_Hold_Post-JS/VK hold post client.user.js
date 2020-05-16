// ==UserScript==
// @name		VK hold post client
// @version		0.2
// @description		Формирует список ссылок с тегами для зарядки очереди
// @author		Seedmanc
// @include		/^https?://vk.com/photo-?\d+_\d+.*$/
// @include		/^https?://vk.com/albums?-?\d+.*z=photo-?\d+_\d+.*$/
// @require		https://code.jquery.com/jquery-3.5.1.slim.min.js
// @grant		GM_addStyle
// @grant		GM_setValue
// @grant		GM_getValue
// @grant		GM_deleteValue
// @grant		GM_listValues
// @noframes
// ==/UserScript==
'use strict';

const Tags = 'kemono_friends kemurikusa cosplay translate@ hentatsu@ keifuku@';
const Group = 'kemono_friends13th';


GM_addStyle (`
	#vkh-wrap {
		position:  fixed;
		display: flex;
		top:       0px;
		z-index:   500;
		max-height: 45px;
	}
	.vkh-button.active {
		font-weight: bold;
	}
	#vkh-buttons {
		display: flex;
		flex-wrap: wrap;
		max-width: 350px;
		max-height: 45px;
	}
	#link-list {
		height: 45px;
		box-sizing: border-box;
	}
	#vkh-del-button {
		margin-left: 5px;
		font-weight: bold;
	}
`);

const Wrap = $('<div id="vkh-wrap"></div>').appendTo(document.body);
const LinkList = $('<textarea id="link-list" wrap="off" cols="53" placeholder="Список ссылок с тегами"/>').appendTo(Wrap);
const AddButton = $('<button style="font-weight: bold;" class="vkh-button">+</button>').appendTo(Wrap);
const TagButtons = $('<div id="vkh-buttons"></div>').appendTo(Wrap);
const DelButton = $('<button id="vkh-del-button">&ndash;</button>').appendTo(Wrap);
const ClrButton = $('<button style="color: red;" title="Удалить всё">╳</button>').appendTo(Wrap);

let links = {};
let url;


(function main() {
	renderTagButtons();
	updateUrl();

	Wrap.click(tagClick);
	DelButton.click(delClick);
	ClrButton.click(clrClick);

	loadList();
	watchUrl();
})();

/**
 * Отслеживать изменения адресной строки при переходе между картинками
 * Нужно для обновления выбранных тегов на кнопках
 */
function watchUrl() { //https://stackoverflow.com/a/46428962/1202246
	let oldHref = document.location.href;
	let observer = new MutationObserver(mutations =>
		mutations.forEach(() => {
			if (oldHref != document.location.href) {
				oldHref = document.location.href;
				updateUrl();
				markButtons();
			}
		})
	);

	let config = {
		childList: true,
		subtree: true
	};
	observer.observe(document.body, config);
}

/**
 * Показать кнопки добавления для указанных в настройках тегов
 */
function renderTagButtons() {
 	let tags = Tags.split(' ').map(t => '#' + t);
	tags.forEach(t => TagButtons.append(
		`<button class="vkh-button" style="flex: 1;" data-tag="${t.replace('@', '@' + Group)}">
			${t}
		</button>`)
	);
}

/**
 * Получить каноничный адрес картинки без протокола, выделив его из обычной или альбомной ссылки
 */
function updateUrl() {
    url = (new URLSearchParams(window.location.search)).get('z');
	if (url)
        url = 'vk.com/' + url.split('/')[0]
    else
        url = document.location.href.match(/.+(vk.com\/photo-?\d+_\d+)/)[1];
}

/**
 * Загрузить из памяти ранее сформированный список ссылок-тегов
 */
function loadList() {
	let storedUrls = GM_listValues();

	storedUrls.forEach(key => links[key] = GM_getValue(key));
	sync();
}

/**
 * Удаление строки с текущей картинкой
 */
function delClick() {
    updateUrl();
	delete links[url];
	GM_deleteValue(url);
	sync();
}

/**
 * Очистить весь список с подтверждением
 * @returns {boolean} - было ли подтверждено удаление
 */
function clrClick() {
	let confirmed = confirm('Очистить весь список?');
	if (confirmed) {
		links = {};
		GM_listValues().forEach(key => GM_deleteValue(key));
		sync();
	}
	return confirmed;
}

/**
 * Добавить текущую картинку в список с выбранным тегом или без тега
 * Либо убрать выбранный тег для текущей картинки, если он уже есть
 * @param {Event} evt - событие клика. Обработчик вешается на родительский контейнер вместо каждой кнопки отдельно, затем проверяется, куда кликали
 */
function tagClick(evt) {
	let target = $(evt.target);
	if (!target.is('.vkh-button')) return;

	updateUrl();

	let tag = target.data('tag');
	let entry = links[url] || {link: url, tags: []};

	if (tag)
		if (entry.tags.includes(tag))
			entry.tags.splice(entry.tags.indexOf(tag), 1)
		else
			entry.tags.push(tag);

	links[url] = entry;
	GM_setValue(url, entry);

	sync();
}

/**
 * Отобразить данные из памяти на экране: обновить текстовое поле со списком и кнопки
 */
function sync() {
	LinkList.val(Object.values(links)
		.map(({link, tags}) => `${link}  ${tags.join(' ')}`).join('\n'));

	markButtons();
}

/**
 * Пометить жирным кнопки с выбранными для текущей картинки тегами
 */
function markButtons() {
	$('.vkh-button').removeClass('active');
	if (links[url])
		links[url].tags.forEach(tag => TagButtons.find(`.vkh-button[data-tag^="${tag}"`).addClass('active'));
}

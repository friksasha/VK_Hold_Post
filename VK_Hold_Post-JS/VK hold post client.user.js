// ==UserScript==
// @name		VK hold post client
// @version		0.3
// @description		Формирует список ссылок с тегами для зарядки очереди
// @author		Seedmanc
// @include		/^https?://vk.com/photo-?\d+_\d+.*$/
// @include		/^https?://vk.com/albums?-?\d+.*z=photo-?\d+_\d+.*$/
// @include		/^https?://vk.com/albums?-?\d+(_\d+)?.*$/
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
	#link-list.vkh-error {
		color: red;
	}
	#vkh-del-button {
		margin-left: 4px;
		font-weight: bold;
	}
`);

const Wrap = $('<div id="vkh-wrap" style="display: none;"></div>').appendTo(document.body);
const LinkList = $('<textarea id="link-list" wrap="off" cols="53" placeholder="Список ссылок с тегами"/>').appendTo(Wrap);
const AddButton = $('<button class="vkh-button">+</button>').appendTo(Wrap);
const TagWrap = $('<div id="vkh-buttons"></div>').appendTo(Wrap);
const DelButton = $('<button id="vkh-del-button">&ndash;</button>').appendTo(Wrap);
const ClrButton = $('<button style="color: red;" title="Удалить всё">╳</button>').appendTo(Wrap);

let links = {};
let url;
const VisiblePages = [/vk.com\/photo-?\d+_\d+/, /^vk.com\/albums?-?\d+.*z=photo-?\d+_\d+/];

(function main() {
	renderTagButtons();
	updateUrl();

	Wrap.click(tagClick);
	DelButton.click(delClick);
	ClrButton.click(clrClick);
	LinkList.change(textChange);
	LinkList.focus(loadList);

	loadList();
	watchUrl();
	toggleGUI();
})();


/**
 * Показывать интерфейс скрипта только на страницах с картинками
 */
function toggleGUI() {
	let visible = VisiblePages.reduce((flag, regexp) => flag || regexp.test(url), false);

	if (visible)
		Wrap.show()
	else
		Wrap.hide();
}

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
				toggleGUI();
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
 * Редактирование тегов и ссылок вручную в текстовом поле
 * Проверяет на корректность ссылку (бросает исключение при ошибке) и теги с разделителями (пытается исправить само)
 */
function textChange() {
	let text = LinkList.val().trim();

	if (!text || !text.split('\n').length)
		if (!clrClick())
			sync();

	LinkList.removeClass('vkh-error');

	try {
		let parsed = text.split('\n').map((line, idx) => {
			let preparsed = line.split(/\s+/);
			let link = preparsed.shift().replace(/https?:\/\//i,'');
			let tags = preparsed.filter(Boolean);

			if (!/^vk\.com\/(photo|album|video|doc)-?\d+_\d+/i.test(link))
				throw 'Неправильная ссылка в строке №' + (idx + 1);

			tags = tags.map(tag => (tag[0] != '#' ? '#' + tag : tag).replace(/@$/, '@' + Group));

			return {link, tags};
		});
		links = {};
		parsed.forEach(({link, tags}) => links[link] = {link, tags});
		sync(true);
	} catch (e) {
		console.error(e);
		LinkList.addClass('vkh-error');
	}
}

/**
 * Показать кнопки добавления для указанных в настройках тегов
 */
function renderTagButtons() {
 	let tags = Tags.split(' ').map(t => '#' + t);
	tags.forEach(t => TagWrap.append(
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
	let matched = document.location.href.match(/.+(vk.com\/photo-?\d+_\d+)/);

	if (url)
		url = 'vk.com/' + url.split('/')[0]
	else
		url = matched && matched[1];
}

/**
 * Загрузить из памяти ранее сформированный список ссылок-тегов
 */
function loadList() {
	if (LinkList.hasClass('vkh-error')) return;

	let storedUrls = GM_listValues();
	links = {};

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
 * @returns {Boolean} - было ли подтверждено удаление
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

	loadList();
}

/**
 * Отобразить данные из памяти на экране: обновить текстовое поле со списком и кнопки
 * @param {Boolean} store - также отправить данные в хранилище
 */
function sync(store) {
	LinkList.val(Object.values(links)
		.map(({link, tags}) => `${link}  ${tags.join(' ')}`).join('\n'));
	markButtons();

	if (store) {
		GM_listValues().forEach(key => GM_deleteValue(key));
		Object.entries(links).forEach(([link, entry]) => GM_setValue(link, entry));
	}
}

/**
 * Пометить жирным кнопки с выбранными для текущей картинки тегами
 */
function markButtons() {
	$('.vkh-button').removeClass('active');
	if (links[url]) {
		AddButton.addClass('active');
		links[url].tags.forEach(tag => TagWrap.find(`.vkh-button[data-tag^="${tag}"`).addClass('active'));
	}
}

// ==UserScript==
// @name		VK hold post client
// @version		0.6
// @description		Формирует список ссылок с тегами для зарядки очереди
// @author		Seedmanc
// @include		/^https?://vk.com/photo-?\d+_\d+.*$/
// @include		/^https?://vk.com/video-?\d+_\d+.*$/
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

// <Настройки>
let TAGS = 'kemono_friends kemurikusa cosplay mmd translate@ hentatsu@ keifuku@'; // все теги
let STAGS = 'cosplay translate@'; // подмножество всех
const GROUP = 'kemono_friends13th';
const POSTS = 6; // постов с обычными тегами в день
const TOKEN = '';
// </Настройки>


GM_addStyle (`
	#vkh-wrap,
	#vkh-scroll {
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
	#vkh-stats {
		background: lightgrey;
   		height: 45px;
		min-width: 168px;
	}
	#line-count {
		position: absolute;
		bottom: 0.3em;
		right: 0.25em;
		pointer-events: none;
	}
	.suggested {
		color: darkcyan;
	}
	#images-wrap {
		margin-left: 4px;
	}
	#images-wrap img {
		width: 45px;
		height: 45px;
		margin-left: 1px;
	}
	#images-wrap a {
		position: relative;
		display: inline-block;
	}
	#images-wrap .vkh-remove {
		position: absolute;
		right: 0;
		color: red;
	}
`);

const Scroll = $('<button id="vkh-scroll">↓</button>').appendTo(document.body);
const Wrap = $('<div id="vkh-wrap" style="display: none;"></div>').appendTo(document.body);
const Stats = $(`<table id="vkh-stats">
	<tr><td title="Обычных / Специальных постов">Заполнено дней (О/С):</td>	<th id="vkh-complete"></th></tr>
	<tr><td title="Обычных / Специальных слотов в незаполненных днях">Пустых слотов (О/С):</td>	<th id="vkh-missing"></th></tr>
</table>`).appendTo(Wrap);
const LinkList = $(`<div style="height: 100%; position: relative;">
	<textarea id="link-list" wrap="off" cols="53" placeholder="Список ссылок с тегами"></textarea> <b id="line-count"></b>
</div>`).appendTo(Wrap).find('#link-list');
const AddButton = $('<button class="vkh-button">+</button>').appendTo(Wrap);
const TagWrap = $('<div id="vkh-buttons"></div>').appendTo(Wrap);
const DelButton = $('<button id="vkh-del-button">&ndash;</button>').appendTo(Wrap);
const ClrButton = $('<button style="color: red;" title="Удалить всё">╳</button>').appendTo(Wrap);
const ImagesWrap = $('<div id="images-wrap"></div>').appendTo(Wrap);

let links = {};
let url, timer;
const VisiblePages = [/vk.com\/photo-?\d+_\d+/, /vk.com\/video-?\d+_\d+/, /^vk.com\/albums?-?\d+.*z=photo-?\d+_\d+/];

(function main() {
	TAGS = formatTags(TAGS);
	STAGS = formatTags(STAGS);

	renderTagButtons();
	updateUrl();

	Wrap.click(tagClick);
	DelButton.click(delClick);
	ClrButton.click(clrClick);
	LinkList.change(textChange);
	LinkList.focus(loadList);
	ImagesWrap.click(removeImage);
	Scroll.click(() => scrollClick(true));

	loadList();
	watchUrl();
	toggleGUI();

	document.addEventListener('visibilitychange', () => {
		if (!document.hidden) {
			loadList();
			if (!$('#images-wrap a').length)
				renderImages();
		}
	});

	unsafeWindow.moveToAlbum = moveToAlbum;
})();


/**
 * Показывать интерфейс скрипта только на страницах с картинками
 */
function toggleGUI() {
	let visible = VisiblePages.reduce((flag, regexp) => flag || regexp.test(url), false);

	if (visible) {
		Scroll.hide();
		Wrap.show();
	} else {
		Wrap.hide();
		if (document.location.href.includes('albums'))
			Scroll.show();
	}
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
				sync();
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

	if (!text || !text.split('\n').filter(Boolean).length) {
	 	ImagesWrap.html('');
	}

	LinkList.removeClass('vkh-error');

	try {
		let parsed = text.split('\n').filter(Boolean).map((line, idx) => {
			let preparsed = line.split(/\s+/);
			let link = preparsed.shift().replace(/https?:\/\//i,'');
			let tags = preparsed.filter(Boolean);

			if (!/^vk\.com\/(photo|album|video|doc)-?\d+_\d+/i.test(link))
				throw 'Неправильная ссылка в строке №' + (idx + 1);

			tags = formatTags(tags);

			return {link, tags};
		});
		links = {};
		parsed.forEach(({link, tags}) => links[link] = {link, tags});
		sync(true);
		renderImages();
	} catch (e) {
		console.error(e);
		LinkList.addClass('vkh-error');
	}
}

/**
 * Дополнить теги # в начале и названием группы после @ в конце
 * @param {String|Array} tagList - список тегов строкой либо массив строк
 * @returns {Array<String>} - массив дополненных тегов
 */
function formatTags(tagList) {
	let array = typeof tagList == 'string' ?
		tagList.split(/\s+/) :
		tagList;
	return array
		.map(t => (t[0] != '#' ? '#' + t : t).replace(/@$/, '@' + GROUP))
		.sort((e1,e2) => STAGS.includes(e2) - STAGS.includes(e1));
}

/**
 * Показать кнопки добавления для указанных в настройках тегов
 */
function renderTagButtons() {
	TAGS.forEach(t => TagWrap.append(
		`<button class="vkh-button" style="flex: 1;${STAGS.includes(t) ? ' text-decoration: underline;' : ''}" data-tag="${t}">
			${t.replace(/@.+$/, '@')}
		</button>`)
	);
}

/**
 * Получить каноничный адрес картинки без протокола, выделив его из обычной или альбомной ссылки
 */
function updateUrl() {
	url = (new URLSearchParams(window.location.search)).get('z');
	let matched = document.location.href.match(/.+(vk.com\/(photo|video)-?\d+_\d+)/);

	if (url)
		url = 'vk.com/' + url.split('/')[0]
	else
		url = matched && matched[1];

	if (/vk\.com\/im/.test(window.location.href))
		url = null;
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
	renderImages();
}

/**
 * Очистить весь список с подтверждением
 * @returns {Boolean} - было ли подтверждено удаление
 */
function clrClick() {
	if (!Object.keys(links).length) return;

	let confirmed = confirm('Очистить весь список?');
	if (confirmed) {
		let lastId = Object.values(links)
			.filter(el => !el.tags.includes('#cosplay'))
			.filter(el => !el.tags.includes('#translate@'+GROUP))
			.map(el => el.link)
			.sort().reverse()[0].split('photo')[1];
		if (document.location.href.includes('albums')) localStorage.vkhLastId = lastId;

		links = {};
		GM_listValues().forEach(key => GM_deleteValue(key));
		sync();
		ImagesWrap.html('');
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

	entry.tags.sort((e1,e2) => STAGS.includes(e2) - STAGS.includes(e1));
	links[url] = entry;
	GM_setValue(url, entry);

	loadList();
	renderImages();
}

/**
 * Отобразить данные из памяти на экране: обновить текстовое поле со списком и кнопки
 * @param {Boolean} store - также отправить данные в хранилище
 */
function sync(store) {
	LinkList.val(Object.values(links)
		.map(({link, tags}) => `${link}  ${tags.join(' ')}`).join('\n'));
	markButtons(countPosts());

	if (store) {
		GM_listValues().forEach(key => GM_deleteValue(key));
		Object.entries(links).forEach(([link, entry]) => GM_setValue(link, entry));
	}
}

/**
 * Пометить жирным кнопки с выбранными для текущей картинки тегами
 * @param {Object, Object} - статистика по спецтегам для пометки недостающих для заполнения
 */
function markButtons({stats, maxSpecial}) {
	$('.vkh-button').removeClass('active suggested');
	let suggestedTags = Object.keys(stats).filter(tag => stats[tag] < maxSpecial);

	if (links[url]) {
		AddButton.addClass('active');
		links[url].tags.forEach(tag => TagWrap.find(`.vkh-button[data-tag^="${tag}"`).addClass('active'));
        suggestedTags = suggestedTags.filter(tag => !links[url].tags.find(t => STAGS.includes(t)));
	}
	suggestedTags.forEach(tag => TagWrap.find(`.vkh-button[data-tag^="${tag}"`).addClass('suggested'));
}

/**
 * Показать статистику по заполненным постами дням и пустующим слотам с учётом категории тегов
 * @returns {Object} - статистика для использования в маркировке кнопок
 */
function countPosts() {
	let lines = Object.values(links);
	let regularPosts = lines.filter(el => !el.tags.find(tag => STAGS.includes(tag)));
	let fullRegular = Math.trunc(regularPosts.length / POSTS);
	let remainingRegular = POSTS - (regularPosts.length % POSTS || POSTS);

	let specialPosts = lines.filter(el => el.tags.find(tag => STAGS.includes(tag)));
	let stats = {};
	STAGS.forEach(tag => {
		stats[tag] = stats[tag] || 0;
		specialPosts		// подсчитывается количество постов по каждому спецтегу, полными днями считаются те, где есть посты с каждым тегом
			.filter(post => post.tags[0] == tag)
			.forEach(post => stats[tag]++)
	});

	let fullSpecial = Math.min(...Object.values(stats));
	let maxSpecial = Math.max(...Object.values(stats));		// пустующие слоты подсчитываются, как количество недостающих до заполнения
	let remainingSpecial = Object.values(stats).reduce((sum, current) => sum + maxSpecial - current, 0);

	Wrap.find('#line-count').text(lines.length);
	Stats.find('#vkh-complete').text(`${fullRegular}/${fullSpecial}`).css('color', fullRegular == fullSpecial ? 'currentColor' : 'orangered');
	Stats.find('#vkh-missing').text(`${remainingRegular}/${remainingSpecial}`).css('color', remainingRegular + remainingSpecial == 0 ? 'currentColor' : 'orangered');

	return {stats, maxSpecial};
}

/**
 * Показать превью для списка ссылок (только картинки)
 */
function renderImages() {
	let ids = LinkList.val().trim().split('\n').filter(link => link && !link.includes('video')).map(link => link.split('/').reverse()[0].match(/-?\d+_\d+/)[0]);
	ImagesWrap.html('');
	if (!ids.length || document.hidden) return;

	fetch(`https://api.vk.com/method/photos.getById?photos=${ids.join(',')}&v=5.52&access_token=${TOKEN}&extended=0&photo_sizes=0`)
		.then(result => result.json())
		.then(r => r.response.forEach(({id, owner_id, photo_75}) => {
			ImagesWrap.append($(`<a href="photo${owner_id}_${id}"><img src="${photo_75}"/><b class="vkh-remove">╳</b></a>`));
		}));
}

/**
 * Удалить ссылку по превью
 */
function removeImage(evt) {
	if ($(evt.target).is('.vkh-remove')) {
		let list = LinkList.val().trim().split('\n');
		let indexToRemove = list.findIndex(line => line.includes($(evt.target).parents('a').attr('href')));
		list.splice(indexToRemove, 1)
		LinkList.val(list.join('\n'));
		textChange();
		return false;
	}
}


/**
 * Переместить набор изображений в альбом
 * @param {String} images - список ссылок на картинки, разделенный переносами строк
 * @param {Number} album - айди альбома, по умолчанию Sandstar Pit
 */
function moveToAlbum(images, album = 261695682) {
	let imgs = images.split('\n').map(el => el.trim().split('_')[1]);

	async function moveImage(id) {
		return await fetch(`https://api.vk.com/method/photos.move?access_token=${TOKEN}&v=5.110&owner_id=-159234408&target_album_id=${album}&photo_id=${id}`)
	}

	const sleep = ms => {
		return new Promise(resolve => setTimeout(resolve, ms))
	}

	(async (imgs) => {for(let i=0; i<imgs.length; i++) {
		await console.log(await moveImage(imgs[i]))
		await sleep(667);
	}})(imgs)
}

/**
 * Найти, где остановились с постингом последний раз в общем списке картинок
 * @param {Boolean} stop - прекратить поиск
 */
function scrollClick(stop) {
	let lastId = localStorage.vkhLastId;
	if (!lastId) return;
	let found = document.querySelector(`[data-id="${lastId}"]`);

	if (stop && timer) {
		window.clearTimeout(timer);
		timer = null;
		return;
	}

	if (found) {
		found.scrollIntoView();
		$(found).css({border:'2px solid #f0f'});
	} else {
		window.scrollTo(0, document.body.scrollHeight);
		timer = setTimeout(scrollClick, 500);
	}
}

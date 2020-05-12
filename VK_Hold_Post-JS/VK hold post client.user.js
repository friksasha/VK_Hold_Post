// ==UserScript==
// @name         VK hold post client
// @version      0.1
// @description  Формирует список ссылок с тегами для зарядки очереди
// @author       Seedmanc
// @include      /^https?://vk.com/photo-?\d+_\d+.*$/
// @include      /^https?://vk.com/albums-?\d+\?z=photo-?\d+_\d+.*$/
// @require  	 https://code.jquery.com/jquery-3.5.1.slim.min.js
// @grant		 GM_addStyle
// @grant		 GM_setValue
// @grant		 GM_getValue
// @grant		 GM_deleteValue
// @grant		 GM_listValues
// @noframes
// ==/UserScript==
'use strict';

const Tags = 'kemono_friends kemurikusa translate@ hentatsu@ keifuku@';
const Group = 'kemono_friends13th';

GM_addStyle (`
	#vkh-wrap {
		position:  fixed;
		display: flex;
		top:       0px;
		left:      0px;
		z-index:   500;
	}
	.vkh-button {
		cursor: pointer;
		flex: 1;
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
		color: red;
		max-height: 45px;
		margin-left: 5px;
	}
`);

const Links = {};

const Wrap = $('<div id="vkh-wrap"></div>').appendTo($("body"));
const LinkList = $('<textarea id="link-list" wrap="off" cols="50" placeholder="Список ссылок с тегами"/>').appendTo(Wrap);
const AddButtons = $('<div id="vkh-buttons"></div>').appendTo(Wrap);
const DelButton = $('<button id="vkh-del-button" class="vkh-button">X</button>').appendTo(Wrap);

let url = (new URLSearchParams(window.location.search)).get('z');


main()

function main() {
	let tags = Tags.split(' ').map(t => '#' + t);
	url = (url ?
           ('vk.com/' + url.split('/')[0]) :
           document.location.href.match(/.+vk.com\/photo-?\d+_\d+/)[0]
    	).replace('https://', '');

	tags.forEach(t => {
		AddButtons.append(`<button id="vkh-${t}" class="vkh-button" data-tag="${t.replace('@', '@' + Group)}">${t}</button>`);
	})

	AddButtons.click(tagClick);
	DelButton.click(delClick);

	loadList();
}


function loadList() {
	let storedUrls = GM_listValues();

	storedUrls.forEach(key => {
		let storedValue = GM_getValue(key);
		Links[key] = {...storedValue, tags: new Set(storedValue.tags)};
	});

	sync(true);
}

function delClick() {
	delete Links[url];
	GM_deleteValue(url);
	sync(true);
}

function tagClick(evt) {
	let target = $(evt.target);
	if (!target.is('.vkh-button')) return;

	let tag = target.data('tag');
	let entry = (Links[url] || {link: url, tags: new Set()});

	if (entry.tags.has(tag))
		entry.tags.delete(tag)
	else
		entry.tags.add(tag);

	Links[url] = entry;
	GM_setValue(url, {...entry, tags: [...entry.tags]});

	sync(true);
}

function sync(out) {
	if (out) {
		LinkList.val(Object.values(Links)
			.map(({link, tags}) => `${link}  ${[...tags].join(' ')}`).join('\n'));

		$('.vkh-button').removeClass('active');
		if (Links[url])
			[...Links[url].tags].forEach(tag => AddButtons.find(`.vkh-button[data-tag^="${tag}"`).addClass('active'));
	}
}

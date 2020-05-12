// ==UserScript==
// @name         VK hold post client
// @version      0.1
// @description  Формирует список ссылок с тегами для зарядки очереди
// @author       Seedmanc
// @include      /^https?://vk.com/photo-?\d+_\d+.*$/
// @require  	 https://code.jquery.com/jquery-3.5.1.slim.min.js
// @grant GM_addStyle
// @noframes
// ==/UserScript==

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
	}
`);

const Links = {};

const Wrap = $("body").append ( `<div id="vkh-wrap"></div>`).find('#vkh-wrap');
const LinkList = Wrap.append ( `<textarea id="link-list" wrap="off" cols="50" placeholder="Список ссылок с тегами"/>` ).find('#link-list');
const AddButtons = Wrap.append('<div id="vkh-buttons"></div>').find('#vkh-buttons');

let url = (new URLSearchParams(window.location.search)).get('z');


main()

function main() {
    'use strict';

	let tags = Tags.split(' ').map(t => '#' + t);
	url = (url ? ('vk.com/' + url.split('/')[0]) : document.location.href.match(/.+vk.com\/photo-?\d+_\d+/)[0]).replace('https://', '');

	tags.forEach(t => {
		AddButtons.append(`<button id="vkh-${t}" class="vkh-button" data-tag="${t.replace('@', '@' + Group)}">${t}</button>`);
	})

	AddButtons.click(evt => {
		let target = $(evt.target);
		if (!target.is('.vkh-button')) return;

		let tag = target.data('tag');
		let entry = (Links[url] || {link: url, tags: new Set()});

		if (entry.tags.has(tag))
			entry.tags.delete(tag)
		else
			entry.tags.add(tag);

		Links[url] = entry;

		sync(true);
	});
}

function sync(out) {
	if (out) {
		LinkList.val(Object.values(Links)
			.map(({link, tags}) => `${link}  ${[...tags].join(' ')}`).join('\n'));

		$('.vkh-button').removeClass('active');
		[...Links[url].tags].forEach(tag => $(`.vkh-button[data-tag^="${tag}"`).addClass('active'));
	}
}
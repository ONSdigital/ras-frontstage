let $jEmitter = $({});

export default class Emitter {

	on(evtName, callback) {
		$jEmitter.on(evtName, (e, data) => callback(data));
	}

	trigger(evtName, data) {
		$jEmitter.trigger(evtName, data);
	}

	static create() {
		return new Emitter();
	}
}

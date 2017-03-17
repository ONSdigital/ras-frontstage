let $jEmitter = $({});

/**
 * Custom event emitter facade
 * @constructor
 */
export default class Emitter {

	/**
	 * Subscribe a callback to a topic of interest
	 * @param evtName
	 * @param callback
	 */
	on(evtName, callback) {
		$jEmitter.on(evtName, (e, data) => callback(data, e));
	}

	/**
	 * Fire an event
	 * @param evtName
	 * @param data
	 */
	trigger(evtName, data) {
		$jEmitter.trigger(evtName, [data, e]);
	}

	static create() {
		return new Emitter();
	}
}

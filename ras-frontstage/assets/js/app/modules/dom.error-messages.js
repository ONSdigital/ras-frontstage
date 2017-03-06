/**
 * Error emitter list
 * @type {Array<Emitter>}
 */
let emitters = [];

export default () => {

}

/**
 * Accepting an error emitter type object
 * @param <Emitter>
 */
export function setErrorEmitter(emitter) {
	emitters.push(emitter);

	emitter.on('error', (e, data) => {
		console.log(data);
	});
}

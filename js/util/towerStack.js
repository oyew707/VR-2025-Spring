
class Stack {
    constructor(maxSize = 9) {
        this.stack = [];
        this.maxSize = maxSize;
    }

    push(element) {
        if (typeof element !== 'object' || element === null || !('value' in element)) {
            throw new Error("Element must be an object with a 'value' property.");
        }

        if (this.stack.length < this.maxSize || this.stack.length === 0 || 
            this.stack[this.stack.length - 1].value > element.value) 
        {
            this.stack.push(element);
            return true;
        }

        return false;
    }

    pop() {
        if (this.stack.length === 0) {
            throw new Error("Stack is empty.");
        }
        return this.stack.pop();
    }

    peek() {
        if (this.stack.length === 0) {
            return null;
        }
        return this.stack[this.stack.length - 1];
    }

    isEmpty() {
        return this.stack.length === 0;
    }

    size() {
        return this.stack.length;
    }
}

export default Stack;

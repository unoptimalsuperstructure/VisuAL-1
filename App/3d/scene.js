const SHAPE_GEOMETRY = {
  UnitCube: {
    vertices: () => {
      const h = 0.5;
      return [[-h,-h,-h],[h,-h,-h],[-h,h,-h],[h,h,-h],[-h,-h,h],[h,-h,h],[-h,h,h],[h,h,h]];
    }
  },
  Point: {
    vertices: (args) => {
      const [x,y,z] = args || [0,0,0];
      return [[x,y,z]];
    }
  }
};

let idCounter = 0;

class SceneObj {
  constructor(type = 'UnitCube', initArgs = null) {
    this.id = ++idCounter;
    this.type = type;
    this.initArgs = initArgs;
    this.vertices = this.getBaseVertices(type, initArgs);
    this.centre = type === 'Point' ? [...this.vertices[0]] : [0, 0, 0];
    this.matrixStack = [[identity4(), 'Identity']];
    this.curMatrix = [identity4(), 'Identity'];
  }

  getBaseVertices(type, args) {
    const shape = SHAPE_GEOMETRY[type] || SHAPE_GEOMETRY['UnitCube'];
    return shape.vertices(args);
  }

  applyTransform(mat, name) {
    this.matrixStack.push([mat, name]);
    this.curMatrix = [matMul4x4(mat, this.curMatrix[0]), name];
    const r = applyMatrix(mat, this.vertices, this.centre);
    this.vertices = r.vertices;
    this.centre = r.centre;
  }

  undo() {
    if (this.matrixStack.length <= 1) return false;
    const inv = invertMatrix4(this.matrixStack[this.matrixStack.length - 1][0]);
    const r = applyMatrix(inv, this.vertices, this.centre);
    this.vertices = r.vertices;
    this.centre = r.centre;
    this.matrixStack.pop();
    return true;
  }

  reset() {
    this.vertices = this.getBaseVertices(this.type, this.initArgs);
    this.centre = this.type === 'Point' ? [...this.vertices[0]] : [0, 0, 0];
    this.matrixStack = [[identity4(), 'Identity']];
    this.curMatrix = [identity4(), 'Identity'];
  }
}


// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.30.0
// 	protoc        v3.21.10
// source: file/file.proto

package file

import (
	common "github.com/openconfig/gnoi/common"
	types "github.com/openconfig/gnoi/types"
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
	protoimpl "google.golang.org/protobuf/runtime/protoimpl"
	reflect "reflect"
	sync "sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

type PutRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	// Types that are assignable to Request:
	//
	//	*PutRequest_Open
	//	*PutRequest_Contents
	//	*PutRequest_Hash
	Request isPutRequest_Request `protobuf_oneof:"request"`
}

func (x *PutRequest) Reset() {
	*x = PutRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *PutRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*PutRequest) ProtoMessage() {}

func (x *PutRequest) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use PutRequest.ProtoReflect.Descriptor instead.
func (*PutRequest) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{0}
}

func (m *PutRequest) GetRequest() isPutRequest_Request {
	if m != nil {
		return m.Request
	}
	return nil
}

func (x *PutRequest) GetOpen() *PutRequest_Details {
	if x, ok := x.GetRequest().(*PutRequest_Open); ok {
		return x.Open
	}
	return nil
}

func (x *PutRequest) GetContents() []byte {
	if x, ok := x.GetRequest().(*PutRequest_Contents); ok {
		return x.Contents
	}
	return nil
}

func (x *PutRequest) GetHash() *types.HashType {
	if x, ok := x.GetRequest().(*PutRequest_Hash); ok {
		return x.Hash
	}
	return nil
}

type isPutRequest_Request interface {
	isPutRequest_Request()
}

type PutRequest_Open struct {
	Open *PutRequest_Details `protobuf:"bytes,1,opt,name=open,proto3,oneof"`
}

type PutRequest_Contents struct {
	Contents []byte `protobuf:"bytes,2,opt,name=contents,proto3,oneof"`
}

type PutRequest_Hash struct {
	Hash *types.HashType `protobuf:"bytes,3,opt,name=hash,proto3,oneof"`
}

func (*PutRequest_Open) isPutRequest_Request() {}

func (*PutRequest_Contents) isPutRequest_Request() {}

func (*PutRequest_Hash) isPutRequest_Request() {}

type PutResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields
}

func (x *PutResponse) Reset() {
	*x = PutResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[1]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *PutResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*PutResponse) ProtoMessage() {}

func (x *PutResponse) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[1]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use PutResponse.ProtoReflect.Descriptor instead.
func (*PutResponse) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{1}
}

type GetRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	RemoteFile string `protobuf:"bytes,1,opt,name=remote_file,json=remoteFile,proto3" json:"remote_file,omitempty"`
}

func (x *GetRequest) Reset() {
	*x = GetRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[2]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetRequest) ProtoMessage() {}

func (x *GetRequest) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[2]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetRequest.ProtoReflect.Descriptor instead.
func (*GetRequest) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{2}
}

func (x *GetRequest) GetRemoteFile() string {
	if x != nil {
		return x.RemoteFile
	}
	return ""
}

type GetResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	// Types that are assignable to Response:
	//
	//	*GetResponse_Contents
	//	*GetResponse_Hash
	Response isGetResponse_Response `protobuf_oneof:"response"`
}

func (x *GetResponse) Reset() {
	*x = GetResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[3]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetResponse) ProtoMessage() {}

func (x *GetResponse) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[3]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetResponse.ProtoReflect.Descriptor instead.
func (*GetResponse) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{3}
}

func (m *GetResponse) GetResponse() isGetResponse_Response {
	if m != nil {
		return m.Response
	}
	return nil
}

func (x *GetResponse) GetContents() []byte {
	if x, ok := x.GetResponse().(*GetResponse_Contents); ok {
		return x.Contents
	}
	return nil
}

func (x *GetResponse) GetHash() *types.HashType {
	if x, ok := x.GetResponse().(*GetResponse_Hash); ok {
		return x.Hash
	}
	return nil
}

type isGetResponse_Response interface {
	isGetResponse_Response()
}

type GetResponse_Contents struct {
	Contents []byte `protobuf:"bytes,1,opt,name=contents,proto3,oneof"`
}

type GetResponse_Hash struct {
	Hash *types.HashType `protobuf:"bytes,2,opt,name=hash,proto3,oneof"`
}

func (*GetResponse_Contents) isGetResponse_Response() {}

func (*GetResponse_Hash) isGetResponse_Response() {}

type TransferToRemoteRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	LocalPath      string                 `protobuf:"bytes,1,opt,name=local_path,json=localPath,proto3" json:"local_path,omitempty"`
	RemoteDownload *common.RemoteDownload `protobuf:"bytes,2,opt,name=remote_download,json=remoteDownload,proto3" json:"remote_download,omitempty"`
}

func (x *TransferToRemoteRequest) Reset() {
	*x = TransferToRemoteRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[4]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *TransferToRemoteRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*TransferToRemoteRequest) ProtoMessage() {}

func (x *TransferToRemoteRequest) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[4]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use TransferToRemoteRequest.ProtoReflect.Descriptor instead.
func (*TransferToRemoteRequest) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{4}
}

func (x *TransferToRemoteRequest) GetLocalPath() string {
	if x != nil {
		return x.LocalPath
	}
	return ""
}

func (x *TransferToRemoteRequest) GetRemoteDownload() *common.RemoteDownload {
	if x != nil {
		return x.RemoteDownload
	}
	return nil
}

type TransferToRemoteResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Hash *types.HashType `protobuf:"bytes,1,opt,name=hash,proto3" json:"hash,omitempty"`
}

func (x *TransferToRemoteResponse) Reset() {
	*x = TransferToRemoteResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[5]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *TransferToRemoteResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*TransferToRemoteResponse) ProtoMessage() {}

func (x *TransferToRemoteResponse) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[5]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use TransferToRemoteResponse.ProtoReflect.Descriptor instead.
func (*TransferToRemoteResponse) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{5}
}

func (x *TransferToRemoteResponse) GetHash() *types.HashType {
	if x != nil {
		return x.Hash
	}
	return nil
}

type StatRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Path string `protobuf:"bytes,1,opt,name=path,proto3" json:"path,omitempty"`
}

func (x *StatRequest) Reset() {
	*x = StatRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[6]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StatRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StatRequest) ProtoMessage() {}

func (x *StatRequest) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[6]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StatRequest.ProtoReflect.Descriptor instead.
func (*StatRequest) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{6}
}

func (x *StatRequest) GetPath() string {
	if x != nil {
		return x.Path
	}
	return ""
}

type StatResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Stats []*StatInfo `protobuf:"bytes,1,rep,name=stats,proto3" json:"stats,omitempty"`
}

func (x *StatResponse) Reset() {
	*x = StatResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[7]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StatResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StatResponse) ProtoMessage() {}

func (x *StatResponse) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[7]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StatResponse.ProtoReflect.Descriptor instead.
func (*StatResponse) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{7}
}

func (x *StatResponse) GetStats() []*StatInfo {
	if x != nil {
		return x.Stats
	}
	return nil
}

type StatInfo struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Path         string `protobuf:"bytes,1,opt,name=path,proto3" json:"path,omitempty"`
	LastModified uint64 `protobuf:"varint,2,opt,name=last_modified,json=lastModified,proto3" json:"last_modified,omitempty"`
	Permissions  uint32 `protobuf:"varint,3,opt,name=permissions,proto3" json:"permissions,omitempty"`
	Size         uint64 `protobuf:"varint,4,opt,name=size,proto3" json:"size,omitempty"`
	Umask        uint32 `protobuf:"varint,5,opt,name=umask,proto3" json:"umask,omitempty"`
}

func (x *StatInfo) Reset() {
	*x = StatInfo{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[8]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StatInfo) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StatInfo) ProtoMessage() {}

func (x *StatInfo) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[8]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StatInfo.ProtoReflect.Descriptor instead.
func (*StatInfo) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{8}
}

func (x *StatInfo) GetPath() string {
	if x != nil {
		return x.Path
	}
	return ""
}

func (x *StatInfo) GetLastModified() uint64 {
	if x != nil {
		return x.LastModified
	}
	return 0
}

func (x *StatInfo) GetPermissions() uint32 {
	if x != nil {
		return x.Permissions
	}
	return 0
}

func (x *StatInfo) GetSize() uint64 {
	if x != nil {
		return x.Size
	}
	return 0
}

func (x *StatInfo) GetUmask() uint32 {
	if x != nil {
		return x.Umask
	}
	return 0
}

type RemoveRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	RemoteFile string `protobuf:"bytes,1,opt,name=remote_file,json=remoteFile,proto3" json:"remote_file,omitempty"`
}

func (x *RemoveRequest) Reset() {
	*x = RemoveRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[9]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *RemoveRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*RemoveRequest) ProtoMessage() {}

func (x *RemoveRequest) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[9]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use RemoveRequest.ProtoReflect.Descriptor instead.
func (*RemoveRequest) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{9}
}

func (x *RemoveRequest) GetRemoteFile() string {
	if x != nil {
		return x.RemoteFile
	}
	return ""
}

type RemoveResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields
}

func (x *RemoveResponse) Reset() {
	*x = RemoveResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[10]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *RemoveResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*RemoveResponse) ProtoMessage() {}

func (x *RemoveResponse) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[10]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use RemoveResponse.ProtoReflect.Descriptor instead.
func (*RemoveResponse) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{10}
}

type PutRequest_Details struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	RemoteFile  string `protobuf:"bytes,1,opt,name=remote_file,json=remoteFile,proto3" json:"remote_file,omitempty"`
	Permissions uint32 `protobuf:"varint,2,opt,name=permissions,proto3" json:"permissions,omitempty"`
}

func (x *PutRequest_Details) Reset() {
	*x = PutRequest_Details{}
	if protoimpl.UnsafeEnabled {
		mi := &file_file_file_proto_msgTypes[11]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *PutRequest_Details) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*PutRequest_Details) ProtoMessage() {}

func (x *PutRequest_Details) ProtoReflect() protoreflect.Message {
	mi := &file_file_file_proto_msgTypes[11]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use PutRequest_Details.ProtoReflect.Descriptor instead.
func (*PutRequest_Details) Descriptor() ([]byte, []int) {
	return file_file_file_proto_rawDescGZIP(), []int{0, 0}
}

func (x *PutRequest_Details) GetRemoteFile() string {
	if x != nil {
		return x.RemoteFile
	}
	return ""
}

func (x *PutRequest_Details) GetPermissions() uint32 {
	if x != nil {
		return x.Permissions
	}
	return 0
}

var File_file_file_proto protoreflect.FileDescriptor

var file_file_file_proto_rawDesc = []byte{
	0x0a, 0x0f, 0x66, 0x69, 0x6c, 0x65, 0x2f, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74,
	0x6f, 0x12, 0x09, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x1a, 0x2e, 0x67, 0x69,
	0x74, 0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x6f, 0x70, 0x65, 0x6e, 0x63, 0x6f, 0x6e,
	0x66, 0x69, 0x67, 0x2f, 0x67, 0x6e, 0x6f, 0x69, 0x2f, 0x63, 0x6f, 0x6d, 0x6d, 0x6f, 0x6e, 0x2f,
	0x63, 0x6f, 0x6d, 0x6d, 0x6f, 0x6e, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x2c, 0x67, 0x69,
	0x74, 0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x6f, 0x70, 0x65, 0x6e, 0x63, 0x6f, 0x6e,
	0x66, 0x69, 0x67, 0x2f, 0x67, 0x6e, 0x6f, 0x69, 0x2f, 0x74, 0x79, 0x70, 0x65, 0x73, 0x2f, 0x74,
	0x79, 0x70, 0x65, 0x73, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x22, 0xe4, 0x01, 0x0a, 0x0a, 0x50,
	0x75, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x33, 0x0a, 0x04, 0x6f, 0x70, 0x65,
	0x6e, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1d, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66,
	0x69, 0x6c, 0x65, 0x2e, 0x50, 0x75, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x2e, 0x44,
	0x65, 0x74, 0x61, 0x69, 0x6c, 0x73, 0x48, 0x00, 0x52, 0x04, 0x6f, 0x70, 0x65, 0x6e, 0x12, 0x1c,
	0x0a, 0x08, 0x63, 0x6f, 0x6e, 0x74, 0x65, 0x6e, 0x74, 0x73, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0c,
	0x48, 0x00, 0x52, 0x08, 0x63, 0x6f, 0x6e, 0x74, 0x65, 0x6e, 0x74, 0x73, 0x12, 0x2a, 0x0a, 0x04,
	0x68, 0x61, 0x73, 0x68, 0x18, 0x03, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x14, 0x2e, 0x67, 0x6e, 0x6f,
	0x69, 0x2e, 0x74, 0x79, 0x70, 0x65, 0x73, 0x2e, 0x48, 0x61, 0x73, 0x68, 0x54, 0x79, 0x70, 0x65,
	0x48, 0x00, 0x52, 0x04, 0x68, 0x61, 0x73, 0x68, 0x1a, 0x4c, 0x0a, 0x07, 0x44, 0x65, 0x74, 0x61,
	0x69, 0x6c, 0x73, 0x12, 0x1f, 0x0a, 0x0b, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x5f, 0x66, 0x69,
	0x6c, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x0a, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65,
	0x46, 0x69, 0x6c, 0x65, 0x12, 0x20, 0x0a, 0x0b, 0x70, 0x65, 0x72, 0x6d, 0x69, 0x73, 0x73, 0x69,
	0x6f, 0x6e, 0x73, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0d, 0x52, 0x0b, 0x70, 0x65, 0x72, 0x6d, 0x69,
	0x73, 0x73, 0x69, 0x6f, 0x6e, 0x73, 0x42, 0x09, 0x0a, 0x07, 0x72, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x22, 0x0d, 0x0a, 0x0b, 0x50, 0x75, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65,
	0x22, 0x2d, 0x0a, 0x0a, 0x47, 0x65, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x1f,
	0x0a, 0x0b, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x5f, 0x66, 0x69, 0x6c, 0x65, 0x18, 0x01, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x0a, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x46, 0x69, 0x6c, 0x65, 0x22,
	0x63, 0x0a, 0x0b, 0x47, 0x65, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x1c,
	0x0a, 0x08, 0x63, 0x6f, 0x6e, 0x74, 0x65, 0x6e, 0x74, 0x73, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0c,
	0x48, 0x00, 0x52, 0x08, 0x63, 0x6f, 0x6e, 0x74, 0x65, 0x6e, 0x74, 0x73, 0x12, 0x2a, 0x0a, 0x04,
	0x68, 0x61, 0x73, 0x68, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x14, 0x2e, 0x67, 0x6e, 0x6f,
	0x69, 0x2e, 0x74, 0x79, 0x70, 0x65, 0x73, 0x2e, 0x48, 0x61, 0x73, 0x68, 0x54, 0x79, 0x70, 0x65,
	0x48, 0x00, 0x52, 0x04, 0x68, 0x61, 0x73, 0x68, 0x42, 0x0a, 0x0a, 0x08, 0x72, 0x65, 0x73, 0x70,
	0x6f, 0x6e, 0x73, 0x65, 0x22, 0x7e, 0x0a, 0x17, 0x54, 0x72, 0x61, 0x6e, 0x73, 0x66, 0x65, 0x72,
	0x54, 0x6f, 0x52, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12,
	0x1d, 0x0a, 0x0a, 0x6c, 0x6f, 0x63, 0x61, 0x6c, 0x5f, 0x70, 0x61, 0x74, 0x68, 0x18, 0x01, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x09, 0x6c, 0x6f, 0x63, 0x61, 0x6c, 0x50, 0x61, 0x74, 0x68, 0x12, 0x44,
	0x0a, 0x0f, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x5f, 0x64, 0x6f, 0x77, 0x6e, 0x6c, 0x6f, 0x61,
	0x64, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1b, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x63,
	0x6f, 0x6d, 0x6d, 0x6f, 0x6e, 0x2e, 0x52, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x44, 0x6f, 0x77, 0x6e,
	0x6c, 0x6f, 0x61, 0x64, 0x52, 0x0e, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x44, 0x6f, 0x77, 0x6e,
	0x6c, 0x6f, 0x61, 0x64, 0x22, 0x44, 0x0a, 0x18, 0x54, 0x72, 0x61, 0x6e, 0x73, 0x66, 0x65, 0x72,
	0x54, 0x6f, 0x52, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65,
	0x12, 0x28, 0x0a, 0x04, 0x68, 0x61, 0x73, 0x68, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x14,
	0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x74, 0x79, 0x70, 0x65, 0x73, 0x2e, 0x48, 0x61, 0x73, 0x68,
	0x54, 0x79, 0x70, 0x65, 0x52, 0x04, 0x68, 0x61, 0x73, 0x68, 0x22, 0x21, 0x0a, 0x0b, 0x53, 0x74,
	0x61, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x12, 0x0a, 0x04, 0x70, 0x61, 0x74,
	0x68, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x04, 0x70, 0x61, 0x74, 0x68, 0x22, 0x39, 0x0a,
	0x0c, 0x53, 0x74, 0x61, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x29, 0x0a,
	0x05, 0x73, 0x74, 0x61, 0x74, 0x73, 0x18, 0x01, 0x20, 0x03, 0x28, 0x0b, 0x32, 0x13, 0x2e, 0x67,
	0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x53, 0x74, 0x61, 0x74, 0x49, 0x6e, 0x66,
	0x6f, 0x52, 0x05, 0x73, 0x74, 0x61, 0x74, 0x73, 0x22, 0x8f, 0x01, 0x0a, 0x08, 0x53, 0x74, 0x61,
	0x74, 0x49, 0x6e, 0x66, 0x6f, 0x12, 0x12, 0x0a, 0x04, 0x70, 0x61, 0x74, 0x68, 0x18, 0x01, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x04, 0x70, 0x61, 0x74, 0x68, 0x12, 0x23, 0x0a, 0x0d, 0x6c, 0x61, 0x73,
	0x74, 0x5f, 0x6d, 0x6f, 0x64, 0x69, 0x66, 0x69, 0x65, 0x64, 0x18, 0x02, 0x20, 0x01, 0x28, 0x04,
	0x52, 0x0c, 0x6c, 0x61, 0x73, 0x74, 0x4d, 0x6f, 0x64, 0x69, 0x66, 0x69, 0x65, 0x64, 0x12, 0x20,
	0x0a, 0x0b, 0x70, 0x65, 0x72, 0x6d, 0x69, 0x73, 0x73, 0x69, 0x6f, 0x6e, 0x73, 0x18, 0x03, 0x20,
	0x01, 0x28, 0x0d, 0x52, 0x0b, 0x70, 0x65, 0x72, 0x6d, 0x69, 0x73, 0x73, 0x69, 0x6f, 0x6e, 0x73,
	0x12, 0x12, 0x0a, 0x04, 0x73, 0x69, 0x7a, 0x65, 0x18, 0x04, 0x20, 0x01, 0x28, 0x04, 0x52, 0x04,
	0x73, 0x69, 0x7a, 0x65, 0x12, 0x14, 0x0a, 0x05, 0x75, 0x6d, 0x61, 0x73, 0x6b, 0x18, 0x05, 0x20,
	0x01, 0x28, 0x0d, 0x52, 0x05, 0x75, 0x6d, 0x61, 0x73, 0x6b, 0x22, 0x30, 0x0a, 0x0d, 0x52, 0x65,
	0x6d, 0x6f, 0x76, 0x65, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x1f, 0x0a, 0x0b, 0x72,
	0x65, 0x6d, 0x6f, 0x74, 0x65, 0x5f, 0x66, 0x69, 0x6c, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09,
	0x52, 0x0a, 0x72, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x46, 0x69, 0x6c, 0x65, 0x22, 0x10, 0x0a, 0x0e,
	0x52, 0x65, 0x6d, 0x6f, 0x76, 0x65, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x32, 0xd5,
	0x02, 0x0a, 0x04, 0x46, 0x69, 0x6c, 0x65, 0x12, 0x38, 0x0a, 0x03, 0x47, 0x65, 0x74, 0x12, 0x15,
	0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x47, 0x65, 0x74, 0x52, 0x65,
	0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x16, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c,
	0x65, 0x2e, 0x47, 0x65, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x00, 0x30,
	0x01, 0x12, 0x5d, 0x0a, 0x10, 0x54, 0x72, 0x61, 0x6e, 0x73, 0x66, 0x65, 0x72, 0x54, 0x6f, 0x52,
	0x65, 0x6d, 0x6f, 0x74, 0x65, 0x12, 0x22, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c,
	0x65, 0x2e, 0x54, 0x72, 0x61, 0x6e, 0x73, 0x66, 0x65, 0x72, 0x54, 0x6f, 0x52, 0x65, 0x6d, 0x6f,
	0x74, 0x65, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x23, 0x2e, 0x67, 0x6e, 0x6f, 0x69,
	0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x54, 0x72, 0x61, 0x6e, 0x73, 0x66, 0x65, 0x72, 0x54, 0x6f,
	0x52, 0x65, 0x6d, 0x6f, 0x74, 0x65, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x00,
	0x12, 0x38, 0x0a, 0x03, 0x50, 0x75, 0x74, 0x12, 0x15, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66,
	0x69, 0x6c, 0x65, 0x2e, 0x50, 0x75, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x16,
	0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x50, 0x75, 0x74, 0x52, 0x65,
	0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x00, 0x28, 0x01, 0x12, 0x39, 0x0a, 0x04, 0x53, 0x74,
	0x61, 0x74, 0x12, 0x16, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x53,
	0x74, 0x61, 0x74, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x17, 0x2e, 0x67, 0x6e, 0x6f,
	0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x53, 0x74, 0x61, 0x74, 0x52, 0x65, 0x73, 0x70, 0x6f,
	0x6e, 0x73, 0x65, 0x22, 0x00, 0x12, 0x3f, 0x0a, 0x06, 0x52, 0x65, 0x6d, 0x6f, 0x76, 0x65, 0x12,
	0x18, 0x2e, 0x67, 0x6e, 0x6f, 0x69, 0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x52, 0x65, 0x6d, 0x6f,
	0x76, 0x65, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x19, 0x2e, 0x67, 0x6e, 0x6f, 0x69,
	0x2e, 0x66, 0x69, 0x6c, 0x65, 0x2e, 0x52, 0x65, 0x6d, 0x6f, 0x76, 0x65, 0x52, 0x65, 0x73, 0x70,
	0x6f, 0x6e, 0x73, 0x65, 0x22, 0x00, 0x42, 0x29, 0xd2, 0x3e, 0x05, 0x30, 0x2e, 0x31, 0x2e, 0x30,
	0x5a, 0x1f, 0x67, 0x69, 0x74, 0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x6f, 0x70, 0x65,
	0x6e, 0x63, 0x6f, 0x6e, 0x66, 0x69, 0x67, 0x2f, 0x67, 0x6e, 0x6f, 0x69, 0x2f, 0x66, 0x69, 0x6c,
	0x65, 0x62, 0x06, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x33,
}

var (
	file_file_file_proto_rawDescOnce sync.Once
	file_file_file_proto_rawDescData = file_file_file_proto_rawDesc
)

func file_file_file_proto_rawDescGZIP() []byte {
	file_file_file_proto_rawDescOnce.Do(func() {
		file_file_file_proto_rawDescData = protoimpl.X.CompressGZIP(file_file_file_proto_rawDescData)
	})
	return file_file_file_proto_rawDescData
}

var file_file_file_proto_msgTypes = make([]protoimpl.MessageInfo, 12)
var file_file_file_proto_goTypes = []interface{}{
	(*PutRequest)(nil),               // 0: gnoi.file.PutRequest
	(*PutResponse)(nil),              // 1: gnoi.file.PutResponse
	(*GetRequest)(nil),               // 2: gnoi.file.GetRequest
	(*GetResponse)(nil),              // 3: gnoi.file.GetResponse
	(*TransferToRemoteRequest)(nil),  // 4: gnoi.file.TransferToRemoteRequest
	(*TransferToRemoteResponse)(nil), // 5: gnoi.file.TransferToRemoteResponse
	(*StatRequest)(nil),              // 6: gnoi.file.StatRequest
	(*StatResponse)(nil),             // 7: gnoi.file.StatResponse
	(*StatInfo)(nil),                 // 8: gnoi.file.StatInfo
	(*RemoveRequest)(nil),            // 9: gnoi.file.RemoveRequest
	(*RemoveResponse)(nil),           // 10: gnoi.file.RemoveResponse
	(*PutRequest_Details)(nil),       // 11: gnoi.file.PutRequest.Details
	(*types.HashType)(nil),           // 12: gnoi.types.HashType
	(*common.RemoteDownload)(nil),    // 13: gnoi.common.RemoteDownload
}
var file_file_file_proto_depIdxs = []int32{
	11, // 0: gnoi.file.PutRequest.open:type_name -> gnoi.file.PutRequest.Details
	12, // 1: gnoi.file.PutRequest.hash:type_name -> gnoi.types.HashType
	12, // 2: gnoi.file.GetResponse.hash:type_name -> gnoi.types.HashType
	13, // 3: gnoi.file.TransferToRemoteRequest.remote_download:type_name -> gnoi.common.RemoteDownload
	12, // 4: gnoi.file.TransferToRemoteResponse.hash:type_name -> gnoi.types.HashType
	8,  // 5: gnoi.file.StatResponse.stats:type_name -> gnoi.file.StatInfo
	2,  // 6: gnoi.file.File.Get:input_type -> gnoi.file.GetRequest
	4,  // 7: gnoi.file.File.TransferToRemote:input_type -> gnoi.file.TransferToRemoteRequest
	0,  // 8: gnoi.file.File.Put:input_type -> gnoi.file.PutRequest
	6,  // 9: gnoi.file.File.Stat:input_type -> gnoi.file.StatRequest
	9,  // 10: gnoi.file.File.Remove:input_type -> gnoi.file.RemoveRequest
	3,  // 11: gnoi.file.File.Get:output_type -> gnoi.file.GetResponse
	5,  // 12: gnoi.file.File.TransferToRemote:output_type -> gnoi.file.TransferToRemoteResponse
	1,  // 13: gnoi.file.File.Put:output_type -> gnoi.file.PutResponse
	7,  // 14: gnoi.file.File.Stat:output_type -> gnoi.file.StatResponse
	10, // 15: gnoi.file.File.Remove:output_type -> gnoi.file.RemoveResponse
	11, // [11:16] is the sub-list for method output_type
	6,  // [6:11] is the sub-list for method input_type
	6,  // [6:6] is the sub-list for extension type_name
	6,  // [6:6] is the sub-list for extension extendee
	0,  // [0:6] is the sub-list for field type_name
}

func init() { file_file_file_proto_init() }
func file_file_file_proto_init() {
	if File_file_file_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_file_file_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*PutRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[1].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*PutResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[2].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[3].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[4].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*TransferToRemoteRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[5].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*TransferToRemoteResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[6].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StatRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[7].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StatResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[8].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StatInfo); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[9].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*RemoveRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[10].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*RemoveResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_file_file_proto_msgTypes[11].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*PutRequest_Details); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	file_file_file_proto_msgTypes[0].OneofWrappers = []interface{}{
		(*PutRequest_Open)(nil),
		(*PutRequest_Contents)(nil),
		(*PutRequest_Hash)(nil),
	}
	file_file_file_proto_msgTypes[3].OneofWrappers = []interface{}{
		(*GetResponse_Contents)(nil),
		(*GetResponse_Hash)(nil),
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_file_file_proto_rawDesc,
			NumEnums:      0,
			NumMessages:   12,
			NumExtensions: 0,
			NumServices:   1,
		},
		GoTypes:           file_file_file_proto_goTypes,
		DependencyIndexes: file_file_file_proto_depIdxs,
		MessageInfos:      file_file_file_proto_msgTypes,
	}.Build()
	File_file_file_proto = out.File
	file_file_file_proto_rawDesc = nil
	file_file_file_proto_goTypes = nil
	file_file_file_proto_depIdxs = nil
}
